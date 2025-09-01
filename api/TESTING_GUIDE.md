# 🧪 Complete Testing Guide for Flash Post API

## Table of Contents

1. [Testing Fundamentals](#testing-fundamentals)
2. [Project Setup](#project-setup)
3. [Writing Your First Test](#writing-your-first-test)
4. [Test Types](#test-types)
5. [Advanced Testing Patterns](#advanced-testing-patterns)
6. [Running Tests](#running-tests)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Testing Fundamentals

### What is Testing?

Testing is the process of verifying that your code works as expected. In software development, we write automated tests to:

- **Verify functionality**: Ensure code does what it's supposed to do
- **Prevent regressions**: Catch bugs when making changes
- **Document behavior**: Tests serve as living documentation
- **Improve design**: Writing tests forces you to think about your API design

### Types of Tests

1. **Unit Tests**: Test individual functions/classes in isolation
2. **Integration Tests**: Test how different parts work together
3. **End-to-End Tests**: Test complete user workflows
4. **Performance Tests**: Test speed and efficiency

## Project Setup

### 1. Install Dependencies

```bash
# Navigate to your API directory
cd /home/emmycool435/project/flash_post/api

# Activate virtual environment
source .venv/bin/activate

# Install test dependencies
uv add --dev pytest-asyncio pytest-cov pytest-mock pytest-timeout
```

### 2. Project Structure

Your test directory should mirror your source structure:

```
api/
├── src/
│   ├── authentication/
│   ├── blogs/
│   ├── models/
│   └── ...
└── test/
    ├── conftest.py          # Global test configuration
    ├── factories/           # Test data factories
    │   ├── user.py
    │   └── blog.py
    ├── fixtures/            # Reusable test components
    ├── integration/         # API endpoint tests
    │   ├── test_auth.py
    │   └── test_blogs.py
    └── unit/               # Service/model tests
        └── test_blog_service.py
```

## Writing Your First Test

### Simple Unit Test Example

```python
# test/unit/test_models.py
import pytest
from src.models.user_model import User
from test.factories.user import UserFactory

class TestUserModel:
    def test_user_creation(self):
        """Test creating a user with UserFactory."""
        user = UserFactory.build()  # Create without saving to DB

        assert user.email is not None
        assert user.first_name is not None
        assert user.last_name is not None
        assert user.role is not None

    def test_user_full_name_property(self):
        """Test the full_name property."""
        user = UserFactory.build(
            first_name="John",
            middle_name="William",
            last_name="Doe"
        )

        assert user.full_name == "John William Doe"

    def test_user_full_name_with_empty_middle(self):
        """Test full_name when middle_name is empty."""
        user = UserFactory.build(
            first_name="Jane",
            middle_name="",
            last_name="Smith"
        )

        assert user.full_name == "Jane Smith"
```

### Simple API Test Example

```python
# test/integration/test_simple_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test the root endpoint."""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Welcome" in data["message"]
```

## Test Types Explained

### 1. Unit Tests

Test individual components in isolation.

```python
# Example: Testing a service function
from unittest.mock import Mock, AsyncMock
from src.blogs.service import BlogService

@pytest.mark.unit
async def test_create_blog_service():
    # Arrange
    mock_db = Mock()
    mock_db.add = Mock()
    mock_db.commit = AsyncMock()

    service = BlogService(db=mock_db)
    blog_data = {"title": "Test", "content": "Content"}

    # Act
    result = await service.create_blog("user-id", blog_data)

    # Assert
    assert result.title == "Test"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
```

### 2. Integration Tests

Test how components work together.

```python
# Example: Testing API endpoint with database
@pytest.mark.integration
async def test_create_blog_endpoint(client: AsyncClient, authenticated_user: dict):
    blog_data = {
        "title": "My Blog Post",
        "content": "This is my blog content"
    }

    response = await client.post(
        "/blogs/",
        json=blog_data,
        headers={"Authorization": f"Bearer {authenticated_user['access_token']}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == blog_data["title"]
```

### 3. Performance Tests

```python
@pytest.mark.performance
async def test_blog_list_performance(client: AsyncClient, seed_database):
    """Test that blog listing performs well with many blogs."""
    import time

    start_time = time.time()
    response = await client.get("/blogs/")
    end_time = time.time()

    assert response.status_code == 200
    assert (end_time - start_time) < 1.0  # Should complete under 1 second
```

## Advanced Testing Patterns

### 1. Parametrized Tests

Test multiple scenarios with the same test function.

```python
@pytest.mark.parametrize("email,password,expected_status", [
    ("valid@email.com", "ValidPass123!", 201),  # Valid
    ("invalid-email", "ValidPass123!", 422),    # Invalid email
    ("valid@email.com", "123", 422),            # Weak password
    ("", "ValidPass123!", 422),                 # Empty email
])
async def test_user_registration_scenarios(
    client: AsyncClient,
    email: str,
    password: str,
    expected_status: int
):
    response = await client.post("/auth/register", json={
        "email": email,
        "password": password,
        "first_name": "Test",
        "last_name": "User"
    })

    assert response.status_code == expected_status
```

### 2. Fixtures for Test Data

```python
@pytest.fixture
async def blog_with_comments(db_session):
    """Create a blog with comments for testing."""
    user = UserFactory.create()
    blog = BlogFactory.create(author=user)
    comments = CommentFactory.create_batch(3, blog=blog, author=user)

    await db_session.commit()

    return {
        "blog": blog,
        "comments": comments,
        "user": user
    }

async def test_blog_with_comments(blog_with_comments):
    blog = blog_with_comments["blog"]
    comments = blog_with_comments["comments"]

    assert len(comments) == 3
    assert all(comment.blog_id == blog.id for comment in comments)
```

### 3. Mocking External Dependencies

```python
from unittest.mock import patch, AsyncMock

@patch('src.notification.service.send_email')
async def test_blog_creation_sends_notification(
    mock_send_email: AsyncMock,
    client: AsyncClient,
    authenticated_user: dict
):
    mock_send_email.return_value = True

    blog_data = {"title": "Test Blog", "content": "Content"}

    response = await client.post(
        "/blogs/",
        json=blog_data,
        headers={"Authorization": f"Bearer {authenticated_user['access_token']}"}
    )

    assert response.status_code == 201
    mock_send_email.assert_called_once()
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest test/integration/test_blogs.py

# Run specific test function
pytest test/integration/test_blogs.py::test_create_blog_success

# Run tests by marker
pytest -m unit          # Run only unit tests
pytest -m integration   # Run only integration tests
pytest -m "not slow"    # Skip slow tests

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run tests in parallel (install pytest-xdist first)
pytest -n auto
```

### Useful Options

```bash
# Stop on first failure
pytest -x

# Stop after N failures
pytest --maxfail=3

# Show local variables in tracebacks
pytest -l

# Run last failed tests only
pytest --lf

# Run modified tests only
pytest --ff

# Capture output (print statements)
pytest -s
```

## Best Practices

### 1. Test Organization

```python
class TestBlogCreation:
    """Group related tests in classes."""

    async def test_valid_blog_creation(self):
        """Test description should be clear."""
        pass

    async def test_invalid_blog_creation(self):
        pass

class TestBlogRetrieval:
    """Another group for different functionality."""

    async def test_get_published_blogs(self):
        pass

    async def test_get_unpublished_blogs(self):
        pass
```

### 2. Clear Test Names

```python
# Good ✅
async def test_create_blog_with_valid_data_returns_201()
async def test_create_blog_without_authentication_returns_401()
async def test_create_blog_with_empty_title_returns_422()

# Bad ❌
async def test_blog()
async def test_create()
async def test_error()
```

### 3. Arrange, Act, Assert Pattern

```python
async def test_user_can_update_own_blog(client, authenticated_user, db_session):
    # Arrange - Set up test data
    blog = BlogFactory.create(author_id=authenticated_user["user"]["id"])
    await db_session.commit()

    update_data = {"title": "Updated Title"}

    # Act - Perform the action
    response = await client.put(
        f"/blogs/{blog.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {authenticated_user['access_token']}"}
    )

    # Assert - Check the results
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
```

### 4. Independent Tests

```python
# Each test should be independent
async def test_blog_creation(db_session):
    # Create fresh data for this test
    user = UserFactory.create()
    await db_session.commit()

    # Test logic here
    pass

# Don't rely on other tests
async def test_blog_update(db_session):
    # Create your own test data
    user = UserFactory.create()
    blog = BlogFactory.create(author=user)
    await db_session.commit()

    # Test logic here
    pass
```

### 5. Test Edge Cases

```python
async def test_blog_creation_scenarios():
    """Test various edge cases."""

    # Empty data
    with pytest.raises(ValidationError):
        BlogFactory.create(title="")

    # Very long title
    with pytest.raises(ValidationError):
        BlogFactory.create(title="a" * 300)

    # None values
    with pytest.raises(ValidationError):
        BlogFactory.create(title=None)
```

## Troubleshooting

### Common Issues

1. **"Event loop is closed" error**

   ```python
   # In conftest.py
   @pytest.fixture(scope="session")
   def event_loop():
       loop = asyncio.new_event_loop()
       asyncio.set_event_loop(loop)
       yield loop
       loop.close()
   ```

2. **Database not cleaned between tests**

   ```python
   @pytest.fixture
   async def db_session(test_engine):
       async with AsyncSession(test_engine) as session:
           yield session
           await session.rollback()  # Important!
   ```

3. **Fixtures not found**
   ```python
   # Make sure __init__.py files exist in test directories
   # Import fixtures in conftest.py
   from .fixtures.user import *
   from .fixtures.database import *
   ```

### Debugging Tests

```python
# Add debug prints
async def test_something(client):
    response = await client.get("/blogs/")
    print(f"Response: {response.json()}")  # Use pytest -s to see output
    assert response.status_code == 200

# Use pytest debugger
async def test_something(client):
    response = await client.get("/blogs/")
    pytest.set_trace()  # Starts debugger
    assert response.status_code == 200

# Use breakpoint (Python 3.7+)
async def test_something(client):
    response = await client.get("/blogs/")
    breakpoint()  # Starts debugger
    assert response.status_code == 200
```

## Quick Start Checklist

- [ ] Install pytest dependencies: `uv add --dev pytest-asyncio pytest-cov`
- [ ] Create test directory structure
- [ ] Set up conftest.py with basic fixtures
- [ ] Create factories for your models
- [ ] Write your first simple test
- [ ] Run the test: `pytest test_file.py -v`
- [ ] Add more test cases
- [ ] Set up CI/CD to run tests automatically

## Example Test Run

```bash
# Complete test run with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing -v

# Results will show:
# - Which tests passed/failed
# - Code coverage percentage
# - Missing lines in coverage
# - HTML report in htmlcov/ directory
```

Remember: **Good tests make good code!** Start simple and gradually add more complex scenarios. Your future self will thank you! 🎉
