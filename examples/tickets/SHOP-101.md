# SHOP-101: Lock user account after failed login attempts

Protect accounts from password guessing.

## Acceptance Criteria
- After 3 consecutive failed login attempts the account is locked
- A locked account cannot log in even with the correct password; the error message is "Account locked, try again in 30 minutes"
- The account is unlocked automatically 30 minutes after it was locked
- A successful login resets the failed attempts counter

## Notes
Lockout duration is fixed for now, configurable later.
