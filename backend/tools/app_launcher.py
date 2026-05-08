from api.system_tasks import match_system_command, run_close_target_action, run_open_target_action, run_system_task


def launch_from_command(text: str) -> str | None:
    close_result = run_close_target_action(text)
    if close_result:
        return close_result

    open_result = run_open_target_action(text)
    if open_result:
        return open_result

    task_id = match_system_command(text)
    if task_id:
        return run_system_task(task_id)

    return None
