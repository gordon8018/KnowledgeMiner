import os
import tempfile
import shutil
import pytest
from unittest.mock import patch, mock_open
from src.utils.file_ops import ensure_dir, copy_file, write_file, read_file, find_markdown_files


class TestFileOps:
    def setup_method(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test.md")
        self.content = "# Test\nThis is a test file.\n"

    def teardown_method(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_ensure_dir_existing(self):
        """Test ensure_dir with existing directory."""
        ensure_dir(self.test_dir)
        assert os.path.exists(self.test_dir)

    def test_ensure_dir_create(self):
        """Test ensure_dir creating new directory."""
        new_dir = os.path.join(self.test_dir, "new", "nested", "directory")
        ensure_dir(new_dir)
        assert os.path.exists(new_dir)

    def test_ensure_dir_file_path(self):
        """Test ensure_dir with file path."""
        write_file(self.test_file, self.content)
        with pytest.raises(OSError):
            ensure_dir(self.test_file)

    def test_copy_file_existing(self):
        """Test copying existing file."""
        write_file(self.test_file, self.content)
        dest_path = os.path.join(self.test_dir, "copy.md")

        result = copy_file(self.test_file, dest_path)
        assert result == True
        assert os.path.exists(dest_path)

        with open(dest_path, 'r') as f:
            assert f.read() == self.content

    def test_copy_file_nonexistent(self):
        """Test copying non-existent file."""
        result = copy_file("nonexistent.md", "dest.md")
        assert result == False

    def test_copy_file_same_source_dest(self):
        """Test copying file to same location."""
        write_file(self.test_file, self.content)
        with pytest.raises(ValueError):
            copy_file(self.test_file, self.test_file)

    def test_copy_file_destination_exists(self):
        """Test copying file when destination exists."""
        write_file(self.test_file, self.content)
        dest_path = os.path.join(self.test_dir, "copy.md")
        write_file(dest_path, "different content")

        result = copy_file(self.test_file, dest_path)
        assert result == True

        with open(dest_path, 'r') as f:
            assert f.read() == self.content

    def test_write_file_create(self):
        """Test write_file creating new file."""
        result = write_file(self.test_file, self.content)
        assert result == True
        assert os.path.exists(self.test_file)

        with open(self.test_file, 'r') as f:
            assert f.read() == self.content

    def test_write_file_overwrite(self):
        """Test write_file overwriting existing file."""
        write_file(self.test_file, "original content")

        result = write_file(self.test_file, self.content)
        assert result == True

        with open(self.test_file, 'r') as f:
            assert f.read() == self.content

    
    def test_read_file_existing(self):
        """Test read_file with existing file."""
        write_file(self.test_file, self.content)

        result = read_file(self.test_file)
        assert result == self.content

    def test_read_file_nonexistent(self):
        """Test read_file with non-existent file."""
        result = read_file("nonexistent.md")
        assert result is None

    def test_read_file_large(self):
        """Test read_file with large file."""
        large_content = "Large content\n" * 1000
        write_file(self.test_file, large_content)

        result = read_file(self.test_file)
        assert result == large_content

    def test_find_markdown_files_current_dir(self):
        """Test find_markdown_files in current directory."""
        write_file(self.test_file, self.content)
        write_file(os.path.join(self.test_dir, "other.txt"), "text content")
        write_file(os.path.join(self.test_dir, "notes.md"), "notes content")

        with patch('os.getcwd', return_value=self.test_dir):
            result = find_markdown_files()
            assert len(result) == 2
            assert os.path.basename(self.test_file) in result
            assert "notes.md" in result

    def test_find_markdown_files_subdirs(self):
        """Test find_markdown_files in subdirectories."""
        subdir = os.path.join(self.test_dir, "subdir")
        os.makedirs(subdir)

        file1 = os.path.join(self.test_dir, "main.md")
        file2 = os.path.join(subdir, "nested.md")
        file3 = os.path.join(self.test_dir, "other.txt")

        write_file(file1, "main content")
        write_file(file2, "nested content")
        write_file(file3, "text content")

        with patch('os.getcwd', return_value=self.test_dir):
            result = find_markdown_files()
            assert len(result) == 2
            assert "main.md" in result
            assert os.path.join("subdir", "nested.md") in result

    def test_find_markdown_files_empty(self):
        """Test find_markdown_files with no markdown files."""
        write_file(os.path.join(self.test_dir, "other.txt"), "text content")

        with patch('os.getcwd', return_value=self.test_dir):
            result = find_markdown_files()
            assert result == []

    def test_find_markdown_files_custom_pattern(self):
        """Test find_markdown_files with custom pattern."""
        write_file(self.test_file, self.content)
        write_file(os.path.join(self.test_dir, "test.txt"), "text content")
        write_file(os.path.join(self.test_dir, "notes.md"), "notes content")

        with patch('os.getcwd', return_value=self.test_dir):
            result = find_markdown_files(pattern="*notes*")
            assert len(result) == 1
            assert "notes.md" in result

    def test_find_markdown_files_recursive_false(self):
        """Test find_markdown_files with recursive=False."""
        subdir = os.path.join(self.test_dir, "subdir")
        os.makedirs(subdir)

        file1 = os.path.join(self.test_dir, "main.md")
        file2 = os.path.join(subdir, "nested.md")
        write_file(file1, "main content")
        write_file(file2, "nested content")

        with patch('os.getcwd', return_value=self.test_dir):
            result = find_markdown_files(recursive=False)
            assert len(result) == 1
            assert "main.md" in result

    def test_file_path_validity(self):
        """Test file path handling for various edge cases."""
        # Test with relative path
        rel_path = os.path.join(self.test_dir, "relative.md")
        write_file(rel_path, "relative content")
        assert os.path.exists(rel_path)

        # Test with path containing spaces
        space_path = os.path.join(self.test_dir, "with spaces.md")
        write_file(space_path, "space content")
        assert os.path.exists(space_path)

    def test_file_encoding(self):
        """Test file operations with different encodings."""
        unicode_content = "Content with unicode: ñáéíóú 中文"
        write_file(self.test_file, unicode_content)

        result = read_file(self.test_file)
        assert result == unicode_content

    @patch('builtins.open', new_callable=mock_open, read_data="mocked content")
    def test_read_file_mock(self, mock_file):
        """Test read_file with mocked file."""
        result = read_file("test.md")
        assert result == "mocked content"

    @patch('builtins.open', new_callable=mock_open)
    def test_write_file_mock(self, mock_file):
        """Test write_file with mocked file."""
        result = write_file("test.md", "content")
        assert result == True
        mock_file.assert_called_once_with("test.md", 'w', encoding='utf-8')

    def test_nested_directory_creation(self):
        """Test writing to nested directory."""
        nested_path = os.path.join(self.test_dir, "deeply", "nested", "path.md")
        content = "Deep nested content"

        result = write_file(nested_path, content)
        assert result == True
        assert os.path.exists(nested_path)

        with open(nested_path, 'r') as f:
            assert f.read() == content