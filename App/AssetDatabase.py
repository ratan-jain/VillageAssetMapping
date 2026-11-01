
import sqlite3


class AssetDatabase:
    def __init__(self, database_path="VillageAssets.db"):
        self.connection = sqlite3.connect(database_path)
        self.connection.row_factory = sqlite3.Row
        self.create_table()

    def create_table(self):
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                village TEXT NOT NULL,
                category TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                owner_type TEXT NOT NULL,
                owner_name TEXT NOT NULL,
                managing_authority TEXT,
                verification_status TEXT NOT NULL
            )
        """)
        self.connection.commit()

    def save_asset(self, asset):
        self.connection.execute("""
            INSERT INTO assets (
                id, name, village, category, latitude, longitude,
                owner_type, owner_name, managing_authority,
                verification_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            asset["id"],
            asset["name"],
            asset["village"],
            asset["category"],
            asset["latitude"],
            asset["longitude"],
            asset["owner_type"],
            asset["owner_name"],
            asset["managing_authority"],
            asset["verification_status"],
        ))
        self.connection.commit()

    def get_asset(self, asset_id):
        row = self.connection.execute(
            "SELECT * FROM assets WHERE id = ?",
            (asset_id,)
        ).fetchone()

        return dict(row) if row else None

    def list_assets(self):
        rows = self.connection.execute(
            "SELECT * FROM assets ORDER BY id"
        ).fetchall()

        return [dict(row) for row in rows]

    def update_asset(self, asset_id, updates):
        allowed_fields = {
            "name", "village", "category", "latitude", "longitude",
            "owner_type", "owner_name", "managing_authority",
            "verification_status",
        }

        if not isinstance(updates, dict) or not updates:
            return False

        if not updates.keys() <= allowed_fields:
            return False

        asset = self.get_asset(asset_id)
        if asset is None:
            return False

        asset.update(updates)

        columns = ", ".join(f"{field} = ?" for field in updates)
        values = list(updates.values()) + [asset_id]

        self.connection.execute(
            f"UPDATE assets SET {columns} WHERE id = ?",
            values
        )
        self.connection.commit()
        return True

    def delete_asset(self, asset_id):
        cursor = self.connection.execute(
            "DELETE FROM assets WHERE id = ?",
            (asset_id,)
        )
        self.connection.commit()
        return cursor.rowcount > 0

    def close(self):
        self.connection.close()
    
    def import_asset(self, asset):
        from DataValidator import validate_asset

        errors = validate_asset(asset)

        if errors:
            return {
                "success": False,
                "errors": errors,
            }

        if self.get_asset(asset["id"]) is not None:
            return {
                "success": False,
                "errors": ["An asset with this ID already exists."],
            }

        try:
            self.save_asset(asset)
        except Exception as error:
            return {
                "success": False,
                "errors": [str(error)],
            }

        return {
            "success": True,
            "asset": asset.copy(),
        }
