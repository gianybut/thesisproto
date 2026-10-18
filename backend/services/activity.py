"""Activity log writer: one row per thing a person did, read on the admin's Activity log page.

Routes call record() after their own commit succeeds. A failure to write the log is printed
and swallowed, so logging can never undo or block the action it describes.
"""

from models import db, ActivityLog
from auth_tokens import current_user

# Action codes and the plain-language name shown for each. GET /api/activity sends this list
# to the web app, so a new code only needs adding here.
ACTIONS = {
    'sign_in': 'Signed in',
    'sign_in_failed': 'Sign-in refused',
    'survey_uploaded': 'Uploaded a survey',
    'survey_renamed': 'Renamed a survey',
    'survey_deleted': 'Deleted a survey',
    'survey_placed': 'Placed a survey on the map',
    'status_changed': 'Changed an inspection status',
    'detection_corrected': 'Corrected a damage record',
    'detection_deleted': 'Deleted a damage record',
    'data_exported': 'Downloaded damage records',
    'report_validated': 'Accepted a resident report',
    'report_rejected': 'Rejected a resident report',
    'account_created': 'Created an account',
    'account_updated': 'Changed an account',
    'password_reset': 'Reset a password',
}


def record(action, summary, target_type=None, target_id=None, user=None, username=None):
    """Write one entry. `user` defaults to the caller; pass username for failed sign-ins."""
    if action not in ACTIONS:
        raise ValueError(f'Unknown activity action: {action}')
    actor = user if user is not None else current_user()
    try:
        db.session.add(ActivityLog(
            user_id=actor.id if actor else None,
            username=actor.username if actor else username,
            action=action,
            target_type=target_type,
            target_id=target_id,
            summary=summary[:500],
        ))
        db.session.commit()
    except Exception as e:  # noqa: BLE001 - the log must never break the action it records
        db.session.rollback()
        print(f"⚠️  Could not write activity log entry ({action}): {e}")
