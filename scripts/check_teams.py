import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.connection import db_manager
from src.database.models import Team

with db_manager.get_session() as session:
    teams = session.query(Team).all()
    print(f"Total teams: {len(teams)}")
    for team in teams:
        print(f"Team: {team.name} - Category: {team.category.value}")
