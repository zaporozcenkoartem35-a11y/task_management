

class UserCreateError(Exception):
    pass

class NoUserError(Exception):
    pass

class IncorrectDeadlineError(Exception):
    pass

class TooManyTasksError(Exception):
    pass

class TaskNotFoundError(Exception):
    pass

class InvalidStatusTransitionError(Exception):
    pass

class CannotCompleteWithoutAssigneeError(Exception):
    pass

class CannotCompleteOverdueError(Exception):
    pass

class CannotEditCompletedTaskError(Exception):
    pass

class CannotChangeAssigneeInReviewError(Exception):
    pass

class CannotDeleteActiveTaskError(Exception):
    pass