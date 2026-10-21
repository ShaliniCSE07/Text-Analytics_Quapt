import os
import csv
import sqlite3

DB_PATH = "data/reviews.db"
CSV_PATH = "data/corrections_log.csv"

def migrate_corrections():
    if not os.path.exists(CSV_PATH):
        print(f"CSV file not found at {CSV_PATH}")
        return 0, 0

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get set of already migrated records by (Platform_Reference_Id, Corrected_At)
    cursor.execute("SELECT Platform_Reference_Id, Corrected_At FROM Review_Corrections")
    existing_records = {(row["Platform_Reference_Id"], row["Corrected_At"]) for row in cursor.fetchall()}

    migrated_count = 0
    skipped_count = 0

    with open(CSV_PATH, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row.get("Platform_Reference_Id", "").strip()
            corrected_at = row.get("Corrected_At", "").strip()

            if not pid:
                continue

            if (pid, corrected_at) in existing_records:
                skipped_count += 1
                continue

            # Fetch Review_Text from Customer_Reviews
            cursor.execute(
                "SELECT Review FROM Customer_Reviews WHERE Platform_Reference_Id = ?",
                (pid,)
            )
            cr_row = cursor.fetchone()
            review_text = cr_row["Review"] if cr_row else ""

            corrected_rating = row.get("Corrected_Rating")
            if corrected_rating == "":
                corrected_rating = None

            corrected_tags = row.get("Corrected_Tags")
            if corrected_tags == "":
                corrected_tags = None

            corrected_by = row.get("Corrected_By")
            if corrected_by == "":
                corrected_by = None

            # Original_Rating and Original_Tags are unknown for these old rows, so store NULL
            cursor.execute(
                """INSERT INTO Review_Corrections (
                    Platform_Reference_Id, Review_Text, Original_Rating, Corrected_Rating,
                    Original_Tags, Corrected_Tags, Corrected_By, Corrected_At, Approved_For_Learning
                ) VALUES (?, ?, NULL, ?, NULL, ?, ?, ?, 1)""",
                (
                    pid,
                    review_text,
                    corrected_rating,
                    corrected_tags,
                    corrected_by,
                    corrected_at
                )
            )
            existing_records.add((pid, corrected_at))
            migrated_count += 1

    conn.commit()
    conn.close()

    print(f"Migrated: {migrated_count}, Skipped: {skipped_count}")
    return migrated_count, skipped_count

if __name__ == "__main__":
    migrate_corrections()
