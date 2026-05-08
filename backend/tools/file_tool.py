from api.system_tasks import extract_file_search, run_local_file_action, search_user_files


def run_file_command(text: str) -> str | None:
    action_result = run_local_file_action(text)
    if action_result:
        return action_result

    query = extract_file_search(text)
    if query:
        return search_user_files(query)

    return None
