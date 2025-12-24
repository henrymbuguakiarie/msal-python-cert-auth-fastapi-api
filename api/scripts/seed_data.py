"""Database seeder script for generating sample blog posts and users.

Usage:
    poetry run python scripts/seed_data.py
    poetry run python scripts/seed_data.py --clear
    poetry run python scripts/seed_data.py --count 50 --users 5
    poetry run python scripts/seed_data.py --clear --count 100 --users 10
"""

import argparse
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from random import choice, randint

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from faker import Faker
from sqlmodel import Session, create_engine, delete, select

from src.config import get_settings
from src.models import BlogPost, User


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Seed the database with sample users and blog posts"
    )
    parser.add_argument(
        "--clear", action="store_true", help="Clear existing data before seeding"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Number of blog posts to create (default: 20)",
    )
    parser.add_argument(
        "--users", type=int, default=3, help="Number of users to create (default: 3)"
    )
    return parser.parse_args()


def clear_database(session: Session) -> None:
    """Clear all existing data from the database.

    Args:
        session: Database session
    """
    print("🗑️  Clearing existing data...")

    # Delete in correct order due to foreign key constraints
    session.exec(delete(BlogPost))
    session.exec(delete(User))
    session.commit()

    print("✅ Database cleared")


def create_users(session: Session, count: int, fake: Faker) -> list[User]:
    """Create sample users.

    Args:
        session: Database session
        count: Number of users to create
        fake: Faker instance

    Returns:
        List of created users
    """
    print(f"\n👥 Creating {count} users...")

    users = []
    for i in range(count):
        user = User(oid=fake.uuid4(), display_name=fake.name())
        session.add(user)
        users.append(user)

    session.commit()

    # Refresh to get IDs
    for user in users:
        session.refresh(user)

    print(f"✅ Created {len(users)} users")
    for user in users:
        print(f"   • {user.display_name} (OID: {user.oid[:8]}...)")

    return users


def create_blog_posts(
    session: Session, users: list[User], count: int, fake: Faker
) -> list[BlogPost]:
    """Create sample blog posts.

    Args:
        session: Database session
        users: List of users to assign as authors
        count: Number of blog posts to create
        fake: Faker instance

    Returns:
        List of created blog posts
    """
    print(f"\n📝 Creating {count} blog posts...")

    posts = []
    now = datetime.now(UTC)

    for i in range(count):
        # Generate realistic blog content
        title = fake.sentence(nb_words=randint(3, 8)).rstrip(".")

        # Generate multiple paragraphs for content
        paragraphs = [
            fake.paragraph(nb_sentences=randint(3, 7)) for _ in range(randint(2, 5))
        ]
        content = "\n\n".join(paragraphs)

        # Assign random author
        author = choice(users)

        # Create post with varied timestamps (spread over last 30 days)
        days_ago = randint(0, 30)
        created_at = now - timedelta(
            days=days_ago, hours=randint(0, 23), minutes=randint(0, 59)
        )

        post = BlogPost(
            title=title,
            content=content,
            author_id=author.id,
            created_at=created_at,
            updated_at=created_at,
        )
        session.add(post)
        posts.append(post)

    session.commit()

    # Refresh to get IDs
    for post in posts:
        session.refresh(post)

    print(f"✅ Created {len(posts)} blog posts")

    # Show post distribution by author
    author_counts = {}
    for post in posts:
        author_name = next(u.display_name for u in users if u.id == post.author_id)
        author_counts[author_name] = author_counts.get(author_name, 0) + 1

    print("\n📊 Posts by author:")
    for author, count in sorted(author_counts.items()):
        print(f"   • {author}: {count} posts")

    return posts


def main():
    """Main seeder function."""
    args = parse_arguments()

    print("🌱 Database Seeder")
    print("=" * 50)

    # Get settings and create engine
    settings = get_settings()
    engine = create_engine(settings.database_url)

    # Initialize Faker
    fake = Faker()
    Faker.seed(42)  # For reproducible data

    with Session(engine) as session:
        # Clear database if requested
        if args.clear:
            clear_database(session)

        # Create users
        users = create_users(session, args.users, fake)

        # Create blog posts
        posts = create_blog_posts(session, users, args.count, fake)

    print("\n" + "=" * 50)
    print(f"✨ Seeding complete!")
    print(f"   Users created: {len(users)}")
    print(f"   Posts created: {len(posts)}")
    print(f"   Database: {settings.database_url}")
    print("\n🚀 You can now test the API with sample data!")


if __name__ == "__main__":
    main()
