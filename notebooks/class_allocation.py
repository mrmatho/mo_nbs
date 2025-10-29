import marimo

__generated_with = "0.16.5"
app = marimo.App(width="full")

with app.setup:
    import marimo as mo
    import pandas as pd
    from pathlib import Path
    from typing import Union, Optional, List, Dict
    import pytest
    import pandas as pd
    import re
    from rapidfuzz import fuzz, process


@app.function
def load_data(file_path: Union[str, Path]) -> pd.DataFrame:
    """
    Load student data from a CSV or Excel file.

    Args:
        file_path (str or Path): Path to the CSV or Excel file

    Returns:
        pd.DataFrame: DataFrame containing student data with columns:
                     'Student Name', 'Friend 1', 'Friend 2', 'Friend 3', 'Friend 4'

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is not supported or required columns are missing
    """
    file_path = Path(file_path)

    # Check if file exists
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Determine file type and load accordingly
    file_extension = file_path.suffix.lower()

    if file_extension == ".csv":
        df = pd.read_csv(file_path)
    elif file_extension in [".xlsx", ".xls"]:
        df = pd.read_excel(file_path, engine="openpyxl")
    else:
        raise ValueError(
            f"Unsupported file format: {file_extension}. Please use .csv, .xlsx, or .xls"
        )

    # Verify required columns are present
    required_columns = [
        "Student Name",
        "Friend 1",
        "Friend 2",
        "Friend 3",
        "Friend 4",
    ]
    missing_columns = [
        col for col in required_columns if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Fill NaN values with empty strings for friend columns
    friend_columns = ["Friend 1", "Friend 2", "Friend 3", "Friend 4"]
    df[friend_columns] = df[friend_columns].fillna("")

    return df


@app.function
def standardize_name(name: Optional[str]) -> str:
    """
    Standardize a name for consistent matching.

    Converts name to lowercase, removes extra whitespace, and handles
    special characters while preserving hyphens and apostrophes.

    Args:
        name (str or None): The name to standardize

    Returns:
        str: Standardized name (lowercase, trimmed whitespace)
             Returns empty string if name is None or empty

    Examples:
        >>> standardize_name("Alice Smith")
        'alice smith'
        >>> standardize_name("  Bob   Jones  ")
        'bob jones'
        >>> standardize_name("Mary-Jane O'Brien")
        'mary-jane o\'brien'
    """
    # Handle None or empty values
    if name is None or (isinstance(name, str) and not name.strip()):
        return ""

    # Convert to string (in case it's not already)
    name = str(name)

    # Convert to lowercase
    name = name.lower()

    # Replace multiple spaces with single space
    name = re.sub(r"\s+", " ", name)

    # Strip leading and trailing whitespace
    name = name.strip()

    return name


@app.function
def build_friendship_graph(df: pd.DataFrame, threshold: float = 85.0) -> Dict[str, List[str]]:
    """
    Build a friendship graph from student data.
    
    Creates a dictionary mapping each student to their list of friends (who are also students).
    Uses fuzzy matching to match friend names entered by students to actual student names.
    
    Args:
        df (pd.DataFrame): DataFrame with columns 'Student Name', 'Friend 1', 'Friend 2', 
                          'Friend 3', 'Friend 4'
        threshold (float): Minimum similarity score (0-100) for fuzzy name matching. Default: 85.0
        
    Returns:
        Dict[str, List[str]]: Dictionary mapping each student name to a list of their friends
                              (friends who are also students in the dataset)
                              
    Examples:
        >>> df = pd.DataFrame({
        ...     'Student Name': ['Alice', 'Bob'],
        ...     'Friend 1': ['Bob', 'Alice'],
        ...     'Friend 2': ['', ''],
        ...     'Friend 3': ['', ''],
        ...     'Friend 4': ['', '']
        ... })
        >>> build_friendship_graph(df)
        {'Alice': ['Bob'], 'Bob': ['Alice']}
    """
    # Initialize graph with all students
    graph = {student: [] for student in df['Student Name']}
    
    # Get list of all student names for matching
    student_list = df['Student Name'].tolist()
    
    # Process each student's friends
    for idx, row in df.iterrows():
        student_name = row['Student Name']
        
        # Collect all friend names for this student
        friend_columns = ['Friend 1', 'Friend 2', 'Friend 3', 'Friend 4']
        friend_names = []
        
        for col in friend_columns:
            friend_value = row[col]
            # Only add non-empty friend names
            if friend_value and str(friend_value).strip():
                friend_names.append(str(friend_value).strip())
        
        # If student has no friends listed, continue to next student
        if not friend_names:
            continue
        
        # Match friend names to actual students using fuzzy matching
        matches = fuzzy_match_friends(friend_names, student_list, threshold)
        
        # Add matched friends to the graph
        for friend_input, matched_student in matches.items():
            # Only add if match was found and it's not the student themselves
            if matched_student and matched_student != student_name:
                graph[student_name].append(matched_student)
    
    return graph


@app.function
def allocate_groups(
    df: pd.DataFrame, 
    friendship_graph: Dict[str, List[str]], 
    num_groups: int = 6
) -> List[List[str]]:
    """
    Allocate students into groups with balanced sizes and friend preferences.
    
    Priority order:
    1. Equal group sizes (target: total_students / num_groups, variance ±1)
    2. At least 1 friend per student (best effort, not guaranteed)
    
    Args:
        df (pd.DataFrame): DataFrame containing student data
        friendship_graph (Dict[str, List[str]]): Mapping of students to their friends
        num_groups (int): Number of groups to create. Default: 6
        
    Returns:
        List[List[str]]: List of groups, where each group is a list of student names
        
    Algorithm:
        - Calculate target group size
        - Sort students by number of friends (fewer friends = higher priority)
        - Attempt to place each student in a group where they have a friend
        - If not possible, place in smallest group
        - Ensure groups stay within ±1 of target size
    """
    students = df['Student Name'].tolist()
    total_students = len(students)
    target_size = total_students // num_groups
    max_size = target_size + (2 if total_students % num_groups > 0 else 0)
    
    # Initialize empty groups
    groups: List[List[str]] = [[] for _ in range(num_groups)]
    
    # Create list of (student, num_friends) for prioritization
    student_priority = []
    for student in students:
        num_friends = len(friendship_graph.get(student, []))
        student_priority.append((student, num_friends))
    
    # Sort by number of friends (ascending) - students with fewer friends get priority
    # This increases chances that students with few friends get their friend match
    student_priority.sort(key=lambda x: x[1])
    
    # Track which students have been allocated
    allocated = set()
    
    # First pass: Try to place students with their friends
    for student, num_friends in student_priority:
        if student in allocated:
            continue
            
        friends = friendship_graph.get(student, [])
        best_group = None
        
        # Try to find a group where this student has a friend
        if friends:
            for group_idx, group in enumerate(groups):
                # Check if group has capacity
                if len(group) >= max_size:
                    continue
                    
                # Check if any friend is in this group
                for friend in friends:
                    if friend in group:
                        best_group = group_idx
                        break
                
                if best_group is not None:
                    break
        
        # If we found a group with a friend and it has capacity, add there
        if best_group is not None:
            groups[best_group].append(student)
            allocated.add(student)
        else:
            # Otherwise, add to the smallest group that has capacity
            # Find group with minimum size that's below max_size
            valid_groups = [(idx, len(group)) for idx, group in enumerate(groups) if len(group) < max_size]
            
            if valid_groups:
                # Sort by size and take the smallest
                valid_groups.sort(key=lambda x: x[1])
                smallest_group_idx = valid_groups[0][0]
                groups[smallest_group_idx].append(student)
                allocated.add(student)
    
    # Second pass: Handle any remaining unallocated students (edge case)
    # This shouldn't happen but just in case
    for student in students:
        if student not in allocated:
            # Find smallest group
            smallest_idx = min(range(num_groups), key=lambda i: len(groups[i]))
            groups[smallest_idx].append(student)
            allocated.add(student)
    
    # Final balancing pass: Try to balance groups within ±1 of target
    # Move students from larger groups to smaller groups if it improves balance
    # and doesn't break friend connections (optional enhancement)
    balance_groups(groups, friendship_graph, target_size)
    
    return groups


@app.function
def balance_groups(
    groups: List[List[str]], 
    friendship_graph: Dict[str, List[str]], 
    target_size: int
) -> None:
    """
    Helper function to balance group sizes while trying to preserve friend connections.
    
    Modifies groups in-place to achieve better balance.
    
    Args:
        groups (List[List[str]]): The groups to balance
        friendship_graph (Dict[str, List[str]]): Friendship connections
        target_size (int): Target size for each group
    """
    max_iterations = 50
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Calculate current group sizes
        sizes = [len(group) for group in groups]
        max_size = max(sizes)
        min_size = min(sizes)
        
        # If groups are balanced within ±1, we're done
        if max_size - min_size <= 1:
            break
        
        # Find largest and smallest groups
        largest_idx = sizes.index(max_size)
        smallest_idx = sizes.index(min_size)
        
        # Try to move a student from largest to smallest
        # Prefer moving students who don't have friends in their current group
        moved = False
        
        for student in groups[largest_idx][:]:  # Create a copy to iterate safely
            friends = friendship_graph.get(student, [])
            
            # Check if student has friends in current group
            has_friends_in_current = any(friend in groups[largest_idx] for friend in friends)
            
            # Check if student would have friends in new group
            would_have_friends_in_new = any(friend in groups[smallest_idx] for friend in friends)
            
            # Move if: no friends in current group, OR would gain friends in new group
            if not has_friends_in_current or would_have_friends_in_new:
                groups[largest_idx].remove(student)
                groups[smallest_idx].append(student)
                moved = True
                break
        
        # If we couldn't find a good candidate, just move anyone
        if not moved and len(groups[largest_idx]) > 0:
            student = groups[largest_idx].pop()
            groups[smallest_idx].append(student)
    
    return None


@app.function
def validate_groups(
    groups: List[List[str]], 
    friendship_graph: Dict[str, List[str]]
) -> Dict[str, any]:
    """
    Validate and analyze the quality of group allocations.
    
    Calculates various metrics about the groups including size distribution,
    friend satisfaction rates, and identifies students without friends in their group.
    
    Args:
        groups (List[List[str]]): List of groups, where each group is a list of student names
        friendship_graph (Dict[str, List[str]]): Mapping of students to their friends
        
    Returns:
        Dict[str, any]: Dictionary containing validation metrics:
            - 'group_sizes': List[int] - Size of each group
            - 'students_with_friends': Dict[int, int] - Count of students with 0, 1, 2, 3, 4 friends
            - 'satisfaction_rate': float - Percentage of students with at least 1 friend (0-100)
            - 'students_with_0_friends': int - Count of students with no friends in their group
            - 'students_without_friends_list': List[str] - Names of students with 0 friends
            - 'total_students': int - Total number of students
            - 'average_friends_per_student': float - Average number of friends per student in their group
            
    Examples:
        >>> groups = [['Alice', 'Bob'], ['Charlie', 'Diana']]
        >>> graph = {'Alice': ['Bob'], 'Bob': ['Alice'], 'Charlie': [], 'Diana': []}
        >>> validate_groups(groups, graph)
        {'group_sizes': [2, 2], 'satisfaction_rate': 50.0, ...}
    """
    validation = {}
    
    # Calculate group sizes
    group_sizes = [len(group) for group in groups]
    validation['group_sizes'] = group_sizes
    validation['total_students'] = sum(group_sizes)
    
    # Track friend counts for each student
    friend_count_distribution = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    students_without_friends = []
    total_friends_in_groups = 0
    
    # Analyze each group
    for group in groups:
        for student in group:
            # Get this student's friends
            student_friends = friendship_graph.get(student, [])
            
            # Count how many of their friends are in the same group
            friends_in_group = [friend for friend in student_friends if friend in group]
            num_friends_in_group = len(friends_in_group)
            
            # Track for average calculation
            total_friends_in_groups += num_friends_in_group
            
            # Cap at 4 for distribution tracking
            capped_count = min(num_friends_in_group, 4)
            friend_count_distribution[capped_count] += 1
            
            # Track students with no friends
            if num_friends_in_group == 0:
                students_without_friends.append(student)
    
    validation['students_with_friends'] = friend_count_distribution
    validation['students_with_0_friends'] = friend_count_distribution[0]
    validation['students_without_friends_list'] = students_without_friends
    
    # Calculate satisfaction rate (percentage with at least 1 friend)
    total_students = validation['total_students']
    if total_students > 0:
        students_with_at_least_one_friend = total_students - friend_count_distribution[0]
        satisfaction_rate = (students_with_at_least_one_friend / total_students) * 100
        validation['satisfaction_rate'] = round(satisfaction_rate, 2)
        
        # Calculate average friends per student
        average_friends = total_friends_in_groups / total_students
        validation['average_friends_per_student'] = round(average_friends, 2)
    else:
        validation['satisfaction_rate'] = 0.0
        validation['average_friends_per_student'] = 0.0
    
    # Add group balance metrics
    if group_sizes:
        validation['min_group_size'] = min(group_sizes)
        validation['max_group_size'] = max(group_sizes)
        validation['group_size_variance'] = max(group_sizes) - min(group_sizes)
    
    return validation


@app.function
def fuzzy_match_friends(
    friend_names: List[str], student_list: List[str], threshold: float = 85.0
) -> Dict[str, Optional[str]]:
    """
    Match friend names to actual student names using fuzzy string matching.

    Uses rapidfuzz library to find the best match for each friend name from
    the list of actual students. Only returns matches above the similarity threshold.

    Args:
        friend_names (List[str]): List of friend names to match (as entered by students)
        student_list (List[str]): List of actual student names
        threshold (float): Minimum similarity score (0-100) to accept a match. Default: 85.0

    Returns:
        Dict[str, Optional[str]]: Dictionary mapping friend names to matched student names
                                   Returns None for friend names with no match above threshold

    Examples:
        >>> students = ['Alice Smith', 'Bob Jones']
        >>> fuzzy_match_friends(['alice smith', 'bob'], students, threshold=80)
        {'alice smith': 'Alice Smith', 'bob': 'Bob Jones'}
    """
    matches = {}

    # Return empty dict if no friends to match
    if not friend_names:
        return matches

    # Create list of tuples: (original_student_name, standardized_student_name)
    student_pairs = [
        (student, standardize_name(student)) for student in student_list
    ]
    standardized_students = [pair[1] for pair in student_pairs]

    for friend_name in friend_names:
        # Skip empty friend names
        if not friend_name or not friend_name.strip():
            continue

        # Standardize the friend name
        std_friend_name = standardize_name(friend_name)

        # Skip if standardized name is empty
        if not std_friend_name:
            continue

        # Find best match using rapidfuzz
        # process.extractOne returns a tuple (match, score, index) or None
        result = process.extractOne(
            std_friend_name,
            standardized_students,
            scorer=fuzz.ratio,
            score_cutoff=threshold,
        )

        # If a match was found above threshold
        if result is not None:
            # Extract the index from the result
            index = result[2]
            # Map back to the original student name using the index
            matches[friend_name] = student_pairs[index][0]
        else:
            # No match found above threshold
            matches[friend_name] = None

    return matches


if __name__ == "__main__":
    app.run()
