
import csv

from AssetManager import AssetManager


class AssetCsvManager:
    def __init__(self, asset_manager):
        self.asset_manager = asset_manager

    def export_assets(self, file_path):
        assets = self.asset_manager.list_assets()

        fieldnames = [
            "id",
            "name",
            "village",
            "category",
            "latitude",
            "longitude",
            "owner_type",
            "owner_name",
            "managing_authority",
            "verification_status",
        ]

        with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=fieldnames,
            )

            writer.writeheader()
            writer.writerows(assets)

        return len(assets)
    
    def import_assets(self, file_path):
        import csv

        imported_count = 0
        errors = []

        with open(
            file_path,
            "r",
            newline="",
            encoding="utf-8-sig",
        ) as csv_file:
            reader = csv.DictReader(csv_file)

            required_headers = {
                "id",
                "name",
                "village",
                "category",
                "latitude",
                "longitude",
                "owner_type",
                "owner_name",
                "managing_authority",
                "verification_status",
            }

            if not reader.fieldnames or not required_headers.issubset(
                reader.fieldnames
            ):
                return {
                    "imported": 0,
                    "errors": ["CSV file is missing required columns."],
                }

            for row_number, row in enumerate(reader, start=2):
                try:
                    row["latitude"] = float(row["latitude"])
                    row["longitude"] = float(row["longitude"])

                    for field in ("id", "name", "village", "category",
                                  "owner_type", "owner_name",
                                  "verification_status"):
                        row[field] = row[field].strip()

                    row["managing_authority"] = (
                        row["managing_authority"].strip() or None
                    )

                    result = self.asset_manager.database.import_asset(row)

                    if result["success"]:
                        imported_count += 1
                    else:
                        errors.append(
                            f"Row {row_number}: "
                            + "; ".join(result["errors"])
                        )

                except (ValueError, TypeError, KeyError) as error:
                    errors.append(
                        f"Row {row_number}: Invalid data - {error}"
                    )

        return {
            "imported": imported_count,
            "errors": errors,
        }
