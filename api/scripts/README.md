# Database Seeder

This script generates sample users and blog posts for local development and testing.

## Usage

### Basic Usage
```bash
# Create 3 users and 20 blog posts (default)
poetry run python scripts/seed_data.py
```

### Clear and Reseed
```bash
# Clear all existing data and create fresh sample data
poetry run python scripts/seed_data.py --clear
```

### Custom Counts
```bash
# Create 5 users and 50 blog posts
poetry run python scripts/seed_data.py --users 5 --count 50

# Clear and create large dataset
poetry run python scripts/seed_data.py --clear --users 10 --count 100
```

### Help
```bash
poetry run python scripts/seed_data.py --help
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--clear` | Clear existing data before seeding | False |
| `--users N` | Number of users to create | 3 |
| `--count N` | Number of blog posts to create | 20 |

## Generated Data

The seeder uses [Faker](https://faker.readthedocs.io/) to generate realistic sample data:

### Users
- **OID**: Random UUID (simulating Microsoft Entra ID user IDs)
- **Display Name**: Random names (e.g., "John Smith", "Jane Doe")

### Blog Posts
- **Title**: Realistic blog post titles (3-8 words)
- **Content**: Multiple paragraphs of lorem ipsum text (2-5 paragraphs)
- **Author**: Randomly assigned from created users
- **Timestamps**: Spread over the last 30 days for realistic data distribution

## Example Output

```
🌱 Database Seeder
==================================================
🗑️  Clearing existing data...
✅ Database cleared

👥 Creating 3 users...
✅ Created 3 users
   • John Smith (OID: a1b2c3d4...)
   • Jane Doe (OID: e5f6g7h8...)
   • Bob Johnson (OID: i9j0k1l2...)

📝 Creating 15 blog posts...
✅ Created 15 blog posts

📊 Posts by author:
   • Bob Johnson: 4 posts
   • Jane Doe: 6 posts
   • John Smith: 5 posts

==================================================
✨ Seeding complete!
   Users created: 3
   Posts created: 15
   Database: sqlite:///./blog_api.db

🚀 You can now test the API with sample data!
```

## Use Cases

1. **Local Development**: Quickly populate your local database for testing API endpoints
2. **Demonstrations**: Show the API working with realistic data
3. **Integration Testing**: Set up test environments with known data sets
4. **Performance Testing**: Generate large datasets to test pagination and query performance

## Notes

- The seeder uses `Faker.seed(42)` for reproducible data generation
- Posts are distributed among authors randomly
- Timestamps are varied to simulate real-world blog activity
- Uses proper foreign key relationships between users and posts
