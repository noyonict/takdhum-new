"""
Import production MySQL backup into local SQLite database.
Usage: python import_prod_db.py
"""
import os
import re
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'takdhum.settings')
django.setup()

from django.db import connection

BACKUP_FILE = 'db_backups/takdhum4_backup_20260314_100718.sql'

# Map production table name -> local table name (where they differ)
TABLE_MAP = {
    'web_subscribe': 'web_subcribe',
}

# Map production column name -> local column name (per table, where they differ)
COLUMN_MAP = {
    'web_subscribe': {'subscriber_email': 'subcriber_email'},
}

# Tables to import (production table names)
IMPORT_TABLES = [
    'auth_user',
    'auth_group',
    'auth_group_permissions',
    'auth_user_groups',
    'auth_user_user_permissions',
    'web_coursecategory',
    'web_courselevel',
    'web_course',
    'web_singlevideo',
    'web_aboutus',
    'web_basic_info',
    'web_slider',
    'web_faq',
    'web_event',
    'web_project',
    'web_testimonial',
    'web_usermessage',
    'web_profile',
    'web_subscribe',
]


def get_local_columns(table_name):
    """Get column names from local SQLite table."""
    with connection.cursor() as cursor:
        cursor.execute(f"PRAGMA table_info(`{table_name}`)")
        return [row[1] for row in cursor.fetchall()]


def parse_backup(backup_file, tables):
    """
    Parse MySQL dump. Returns:
      create_cols[table] = [col, col, ...]  (from CREATE TABLE)
      inserts[table]     = [stmt, stmt, ...]
    """
    create_cols = {}
    inserts = {t: [] for t in tables}
    current_table = None
    in_create = False
    create_lines = []

    with open(backup_file, 'r', encoding='utf-8', errors='replace') as f:
        for raw in f:
            line = raw.rstrip('\n')

            # Detect CREATE TABLE start
            m = re.match(r"CREATE TABLE `(\w+)`", line)
            if m:
                current_table = m.group(1)
                in_create = True
                create_lines = []
                continue

            if in_create:
                if line.startswith(')'):
                    in_create = False
                    # Parse column names from accumulated lines
                    cols = []
                    for cl in create_lines:
                        cl = cl.strip()
                        # Column lines start with backtick
                        cm = re.match(r'`(\w+)`', cl)
                        if cm and not cl.startswith('KEY') and not cl.startswith('PRIMARY') \
                                and not cl.startswith('UNIQUE') and not cl.startswith('CONSTRAINT'):
                            cols.append(cm.group(1))
                    if current_table in tables:
                        create_cols[current_table] = cols
                    current_table = None
                else:
                    create_lines.append(line)
                continue

            # Track LOCK/UNLOCK
            m = re.match(r"LOCK TABLES `(\w+)` WRITE", line)
            if m:
                current_table = m.group(1)
                continue

            if line.startswith('UNLOCK TABLES'):
                current_table = None
                continue

            # Collect INSERT statements for wanted tables
            if current_table in tables and line.startswith('INSERT INTO'):
                inserts[current_table].append(line)

    return create_cols, inserts


def mysql_string_to_sqlite(val):
    """
    Convert a MySQL-escaped SQL string value to SQLite-compatible form.
    MySQL uses backslash escapes inside strings; SQLite uses '' for single quotes.
    Input/output: the full value token including surrounding quotes, e.g. 'it\\'s'
    """
    if not (val.startswith("'") and val.endswith("'")):
        return val  # not a string (NULL, number, etc.)

    inner = val[1:-1]  # strip surrounding quotes

    # Decode MySQL escape sequences into the actual characters
    result = []
    i = 0
    while i < len(inner):
        c = inner[i]
        if c == '\\' and i + 1 < len(inner):
            nc = inner[i + 1]
            if nc == "'":
                result.append("'")
            elif nc == '\\':
                result.append('\\')
            elif nc == 'n':
                result.append('\n')
            elif nc == 'r':
                result.append('\r')
            elif nc == 't':
                result.append('\t')
            elif nc == '0':
                result.append('\x00')
            else:
                result.append(nc)
            i += 2
        else:
            result.append(c)
            i += 1

    # Re-escape for SQLite: single quotes become ''
    sqlite_inner = ''.join(result).replace("'", "''")
    return f"'{sqlite_inner}'"


def split_row(row_content):
    """
    Split a MySQL VALUES row (content between outer parens) into individual values.
    Handles quoted strings with backslash escapes and NULL/numbers.
    """
    vals = []
    current = []
    in_str = False
    escape = False

    for c in row_content:
        if escape:
            current.append(c)
            escape = False
        elif c == '\\' and in_str:
            current.append(c)
            escape = True
        elif c == "'" and not in_str:
            in_str = True
            current.append(c)
        elif c == "'" and in_str:
            in_str = False
            current.append(c)
        elif c == ',' and not in_str:
            vals.append(''.join(current).strip())
            current = []
        else:
            current.append(c)

    if current:
        vals.append(''.join(current).strip())
    return vals


def extract_rows(values_part):
    """
    Extract all (row) tuples from the VALUES section of a MySQL INSERT.
    Handles nested parentheses inside quoted strings.
    """
    rows = []
    i = 0
    while i < len(values_part):
        if values_part[i] == '(':
            # Find matching closing paren, respecting quoted strings
            depth = 0
            in_str = False
            escape = False
            j = i
            while j < len(values_part):
                c = values_part[j]
                if escape:
                    escape = False
                elif c == '\\' and in_str:
                    escape = True
                elif c == "'" and not in_str:
                    in_str = True
                elif c == "'" and in_str:
                    in_str = False
                elif c == '(' and not in_str:
                    depth += 1
                elif c == ')' and not in_str:
                    depth -= 1
                    if depth == 0:
                        rows.append(values_part[i+1:j])  # content without parens
                        i = j
                        break
                j += 1
        i += 1
    return rows


def rewrite_insert(stmt, local_table, prod_cols, local_cols, col_map=None):
    """
    Rewrite a MySQL INSERT statement for SQLite:
    - rename table
    - add explicit column list (handles extra/missing columns)
    - apply column name mapping
    - convert MySQL string escapes to SQLite format
    """
    col_map = col_map or {}
    local_col_set = set(local_cols)

    # Map prod column names through col_map, keep only those in local schema
    keep_indices = []
    keep_cols = []
    for i, c in enumerate(prod_cols):
        mapped = col_map.get(c, c)
        if mapped in local_col_set:
            keep_indices.append(i)
            keep_cols.append(mapped)

    if not keep_cols:
        return None

    col_clause = ', '.join(f'`{c}`' for c in keep_cols)

    # Strip "INSERT INTO `table` VALUES " prefix and trailing semicolon
    values_part = re.sub(r'^INSERT INTO `\w+` VALUES\s*', '', stmt).rstrip(';').strip()

    rows = extract_rows(values_part)
    new_rows = []
    for row_content in rows:
        vals = split_row(row_content)
        if len(vals) < len(prod_cols):
            continue
        picked = [mysql_string_to_sqlite(vals[i]) for i in keep_indices]
        new_rows.append('(' + ','.join(picked) + ')')

    if not new_rows:
        return None

    return f"INSERT OR REPLACE INTO `{local_table}` ({col_clause}) VALUES {','.join(new_rows)}"


def main():
    print(f"Reading backup: {BACKUP_FILE}")
    create_cols, inserts = parse_backup(BACKUP_FILE, IMPORT_TABLES)

    print("\nProduction table columns found:")
    for t, cols in create_cols.items():
        print(f"  {t}: {len(cols)} cols")

    # Clear local tables (reverse order to respect FKs)
    print("\nClearing local tables...")
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = OFF")
        for prod_table in reversed(IMPORT_TABLES):
            local_table = TABLE_MAP.get(prod_table, prod_table)
            try:
                cursor.execute(f"DELETE FROM `{local_table}`")
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{local_table}'")
            except Exception:
                pass

    # Import each table
    print("\nImporting data...")
    with connection.cursor() as cursor:
        for prod_table in IMPORT_TABLES:
            local_table = TABLE_MAP.get(prod_table, prod_table)
            prod_cols = create_cols.get(prod_table, [])
            local_cols = get_local_columns(local_table)

            if not prod_cols:
                print(f"  {prod_table}: no schema found in backup, skipping")
                continue

            stmts = inserts.get(prod_table, [])
            if not stmts:
                print(f"  {prod_table} → {local_table}: 0 rows (empty table in production)")
                continue

            col_map = COLUMN_MAP.get(prod_table, {})
            ok = err = 0
            for stmt in stmts:
                rewritten = rewrite_insert(stmt, local_table, prod_cols, local_cols, col_map)
                if not rewritten:
                    continue
                try:
                    cursor.execute(rewritten)
                    ok += 1
                except Exception as e:
                    err += 1
                    if err <= 2:
                        print(f"    ERROR in {prod_table}: {e}")

            prefix = f"{prod_table}" if prod_table == local_table else f"{prod_table} → {local_table}"
            print(f"  {prefix}: {ok} batches imported ({err} errors)")

        cursor.execute("PRAGMA foreign_keys = ON")

    print("\nDone! Local database updated with production data.")
    print("Run: venv/bin/python manage.py runserver")


if __name__ == '__main__':
    main()
