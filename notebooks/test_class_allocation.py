from class_allocation import (
    load_data,
    standardize_name,
    fuzzy_match_friends,
    build_friendship_graph,
    allocate_groups,
    validate_groups
)

import pytest
import pandas as pd

# Test Data Fixtures
@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing"""
    data = {
        'Student Name': ['Alice Smith', 'Bob Jones', 'Charlie Brown', 'Diana Prince', 'Eve Wilson', 'Frank Castle'],
        'Friend 1': ['bob jones', 'Alice Smith', 'Bob Jones', 'eve wilson', 'Diana Prince', 'Charlie Brown'],
        'Friend 2': ['Charlie Brown', 'charlie', 'Alice', 'Frank Castle', 'Alice Smith', ''],
        'Friend 3': ['', 'Diana Prince', '', '', 'Bob Jones', 'Bob Jones'],
        'Friend 4': ['', '', '', '', '', '']
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_csv_file(tmp_path, sample_df):
    """Create a temporary CSV file for testing"""
    csv_file = tmp_path / "students.csv"
    sample_df.to_csv(csv_file, index=False)
    return csv_file


@pytest.fixture
def sample_excel_file(tmp_path, sample_df):
    """Create a temporary Excel file for testing"""
    excel_file = tmp_path / "students.xlsx"
    sample_df.to_excel(excel_file, index=False)
    return excel_file


# Test 1: Data Loading
class TestDataLoading:
    def test_load_csv_file(self, sample_csv_file):
        """Test loading a CSV file"""
        df = load_data(sample_csv_file)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 6
        assert 'Student Name' in df.columns
        
    def test_load_excel_file(self, sample_excel_file):
        """Test loading an Excel file"""
        df = load_data(sample_excel_file)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 6
        assert 'Student Name' in df.columns
    
    def test_load_nonexistent_file(self):
        """Test that loading a nonexistent file raises an error"""
        with pytest.raises(FileNotFoundError):
            load_data("nonexistent_file.csv")
    
    def test_columns_present(self, sample_csv_file):
        """Test that all required columns are present"""
        df = load_data(sample_csv_file)
        required_columns = ['Student Name', 'Friend 1', 'Friend 2', 'Friend 3', 'Friend 4']
        for col in required_columns:
            assert col in df.columns


# Test 2: Name Standardization
class TestNameStandardization:
    def test_standardize_basic_name(self):
        """Test basic name standardization"""
        assert standardize_name("Alice Smith") == "alice smith"
    
    def test_standardize_extra_whitespace(self):
        """Test removing extra whitespace"""
        assert standardize_name("  Bob   Jones  ") == "bob jones"
    
    def test_standardize_mixed_case(self):
        """Test handling mixed case"""
        assert standardize_name("ChArLiE BrOwN") == "charlie brown"
    
    def test_standardize_special_characters(self):
        """Test handling special characters"""
        # Should keep hyphens and apostrophes
        assert standardize_name("Mary-Jane O'Brien") == "mary-jane o'brien"
    
    def test_standardize_empty_string(self):
        """Test handling empty strings"""
        assert standardize_name("") == ""
    
    def test_standardize_none(self):
        """Test handling None values"""
        assert standardize_name(None) == ""


# Test 3: Fuzzy Name Matching
class TestFuzzyMatching:
    def test_exact_match(self, sample_df):
        """Test exact name matching"""
        students = sample_df['Student Name'].tolist()
        matches = fuzzy_match_friends(['Alice Smith'], students, threshold=85)
        assert matches['Alice Smith'] == 'Alice Smith'
    
    def test_fuzzy_match_different_case(self, sample_df):
        """Test fuzzy matching with different case"""
        students = sample_df['Student Name'].tolist()
        matches = fuzzy_match_friends(['alice smith'], students, threshold=85)
        assert matches['alice smith'] == 'Alice Smith'
    
    def test_fuzzy_match_partial_name(self, sample_df):
        """Test fuzzy matching with partial names"""
        students = sample_df['Student Name'].tolist()
        matches = fuzzy_match_friends(['bob'], students, threshold=50)
        assert matches['bob'] == 'Bob Jones'
    
    def test_no_match_below_threshold(self, sample_df):
        """Test that names below threshold don't match"""
        students = sample_df['Student Name'].tolist()
        matches = fuzzy_match_friends(['xyz'], students, threshold=85)
        assert 'xyz' not in matches or matches['xyz'] is None
    
    def test_empty_friend_list(self, sample_df):
        """Test handling empty friend list"""
        students = sample_df['Student Name'].tolist()
        matches = fuzzy_match_friends([], students, threshold=85)
        assert matches == {}
    
    def test_multiple_friends(self, sample_df):
        """Test matching multiple friends at once"""
        students = sample_df['Student Name'].tolist()
        matches = fuzzy_match_friends(['alice smith', 'bob jones', 'charlie'], students, threshold=75)
        assert len(matches) >= 2  # At least Alice and Bob should match


# Test 4: Friendship Graph Building
class TestFriendshipGraph:
    def test_build_basic_graph(self, sample_df):
        """Test building a basic friendship graph"""
        graph = build_friendship_graph(sample_df, threshold=85)
        assert isinstance(graph, dict)
        assert len(graph) == len(sample_df)
    
    def test_graph_contains_all_students(self, sample_df):
        """Test that graph contains all students"""
        graph = build_friendship_graph(sample_df, threshold=85)
        student_names = sample_df['Student Name'].tolist()
        for student in student_names:
            assert student in graph
    
    def test_friendship_is_list(self, sample_df):
        """Test that each student's friends is a list"""
        graph = build_friendship_graph(sample_df, threshold=85)
        for student, friends in graph.items():
            assert isinstance(friends, list)
    
    def test_no_self_friendship(self, sample_df):
        """Test that students aren't listed as their own friends"""
        graph = build_friendship_graph(sample_df, threshold=85)
        for student, friends in graph.items():
            assert student not in friends
    
    def test_empty_friends_handled(self):
        """Test handling students with no valid friends"""
        df = pd.DataFrame({
            'Student Name': ['Alice'],
            'Friend 1': [''],
            'Friend 2': [''],
            'Friend 3': [''],
            'Friend 4': ['']
        })
        graph = build_friendship_graph(df, threshold=85)
        assert graph['Alice'] == []


# Test 5: Group Allocation
class TestGroupAllocation:
    def test_allocate_creates_six_groups(self, sample_df):
        """Test that allocation creates exactly 6 groups"""
        graph = build_friendship_graph(sample_df, threshold=85)
        groups = allocate_groups(sample_df, graph, num_groups=6)
        assert len(groups) == 6
    
    def test_all_students_allocated(self, sample_df):
        """Test that all students are allocated to a group"""
        graph = build_friendship_graph(sample_df, threshold=85)
        groups = allocate_groups(sample_df, graph, num_groups=6)
        total_students = sum(len(group) for group in groups)
        assert total_students == len(sample_df)
    
    def test_no_duplicate_students(self, sample_df):
        """Test that no student appears in multiple groups"""
        graph = build_friendship_graph(sample_df, threshold=85)
        groups = allocate_groups(sample_df, graph, num_groups=6)
        all_students = []
        for group in groups:
            all_students.extend(group)
        assert len(all_students) == len(set(all_students))
    
    def test_group_sizes_balanced(self, sample_df):
        """Test that group sizes are roughly balanced"""
        graph = build_friendship_graph(sample_df, threshold=85)
        groups = allocate_groups(sample_df, graph, num_groups=6)
        group_sizes = [len(group) for group in groups]
        assert max(group_sizes) - min(group_sizes) <= 1
    
    def test_larger_dataset_balance(self):
        """Test balanced groups with more students"""
        # Create 30 students (5 per group ideal)
        students = [f"Student {i}" for i in range(30)]
        df = pd.DataFrame({
            'Student Name': students,
            'Friend 1': [''] * 30,
            'Friend 2': [''] * 30,
            'Friend 3': [''] * 30,
            'Friend 4': [''] * 30
        })
        graph = build_friendship_graph(df, threshold=85)
        groups = allocate_groups(df, graph, num_groups=6)
        group_sizes = [len(group) for group in groups]
        # All groups should be size 5
        assert all(size == 5 for size in group_sizes)


# Test 6: Group Validation
class TestGroupValidation:
    def test_validation_returns_dict(self, sample_df):
        """Test that validation returns a dictionary of metrics"""
        graph = build_friendship_graph(sample_df, threshold=85)
        groups = allocate_groups(sample_df, graph, num_groups=6)
        validation = validate_groups(groups, graph)
        assert isinstance(validation, dict)
    
    def test_validation_has_required_metrics(self, sample_df):
        """Test that validation includes all required metrics"""
        graph = build_friendship_graph(sample_df, threshold=85)
        groups = allocate_groups(sample_df, graph, num_groups=6)
        validation = validate_groups(groups, graph)
        required_keys = ['group_sizes', 'students_with_friends', 'satisfaction_rate']
        for key in required_keys:
            assert key in validation
    
    def test_group_sizes_correct(self, sample_df):
        """Test that reported group sizes are correct"""
        graph = build_friendship_graph(sample_df, threshold=85)
        groups = allocate_groups(sample_df, graph, num_groups=6)
        validation = validate_groups(groups, graph)
        assert len(validation['group_sizes']) == 6
        assert sum(validation['group_sizes']) == len(sample_df)
    
    def test_satisfaction_rate_range(self, sample_df):
        """Test that satisfaction rate is between 0 and 100"""
        graph = build_friendship_graph(sample_df, threshold=85)
        groups = allocate_groups(sample_df, graph, num_groups=6)
        validation = validate_groups(groups, graph)
        assert 0 <= validation['satisfaction_rate'] <= 100
    
    def test_students_with_zero_friends(self):
        """Test identifying students with no friends in their group"""
        # Create scenario where some students have no friends
        df = pd.DataFrame({
            'Student Name': ['A', 'B', 'C', 'D', 'E', 'F'],
            'Friend 1': ['B', 'A', '', '', '', ''],
            'Friend 2': ['', '', '', '', '', ''],
            'Friend 3': ['', '', '', '', '', ''],
            'Friend 4': ['', '', '', '', '', '']
        })
        graph = build_friendship_graph(df, threshold=85)
        groups = allocate_groups(df, graph, num_groups=6)
        validation = validate_groups(groups, graph)
        # Should track how many students have 0 friends in group
        assert 'students_with_0_friends' in validation
        assert validation['students_with_0_friends'] >= 0


# Test 7: Edge Cases
class TestEdgeCases:
    def test_single_student(self):
        """Test handling a single student"""
        df = pd.DataFrame({
            'Student Name': ['Alice'],
            'Friend 1': [''], 'Friend 2': [''], 'Friend 3': [''], 'Friend 4': ['']
        })
        graph = build_friendship_graph(df, threshold=85)
        groups = allocate_groups(df, graph, num_groups=6)
        # Should have 6 groups, 5 empty
        assert len(groups) == 6
        assert sum(len(g) for g in groups) == 1
    
    def test_all_students_friends_with_each_other(self):
        """Test when all students list each other as friends"""
        students = ['A', 'B', 'C', 'D', 'E', 'F']
        df = pd.DataFrame({
            'Student Name': students,
            'Friend 1': ['B', 'A', 'A', 'A', 'A', 'A'],
            'Friend 2': ['C', 'C', 'B', 'B', 'B', 'B'],
            'Friend 3': ['D', 'D', 'D', 'C', 'C', 'C'],
            'Friend 4': ['E', 'E', 'E', 'E', 'D', 'D']
        })
        graph = build_friendship_graph(df, threshold=85)
        groups = allocate_groups(df, graph, num_groups=6)
        validation = validate_groups(groups, graph)
        # With many friendships, satisfaction should be high
        assert validation['satisfaction_rate'] >= 50
    
    def test_no_matching_friends(self):
        """Test when no friend names match actual students"""
        df = pd.DataFrame({
            'Student Name': ['Alice', 'Bob', 'Charlie'],
            'Friend 1': ['xyz', 'abc', 'def'],
            'Friend 2': ['', '', ''],
            'Friend 3': ['', '', ''],
            'Friend 4': ['', '', '']
        })
        graph = build_friendship_graph(df, threshold=85)
        # All students should have empty friend lists
        assert all(len(friends) == 0 for friends in graph.values())