"""Connection script for interactive connection."""
import os
from sqlalchemy.orm import Session
from gymbuddies import database
from gymbuddies.database import db

s = Session(db.engine)
print("Imported modules:")
print("\n".join("\t" + str(c) for c in (database, db, Session)))
print(f"Created a Session {s = } on {db.engine = }")
print(f"This module should be used in interactively via 'python -i {os.path.basename(__file__)}'.")
