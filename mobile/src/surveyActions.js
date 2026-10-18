// What the survey list and the survey screen both do to a survey.
import { Alert } from 'react-native';
import { deleteSession } from './storage';
import { cancelUpload, enqueue } from './uploadQueue';
import { surveyTitle } from './labels';

/** Delete with the web's wording; shared with the survey screen. */
export function confirmDelete(item, onDeleted) {
  const unsent = item.status !== 'uploaded' && !item.broken;
  Alert.alert(
    `Delete ${surveyTitle(item)}?`,
    unsent
      ? 'This survey has not been uploaded. The video and GPS track will be gone for good.'
      : 'The video and GPS track will be removed from this phone. The uploaded copy stays on the web app.',
    [
      { text: 'Keep', style: 'cancel' },
      {
        text: 'Delete survey', style: 'destructive',
        onPress: () => { cancelUpload(item.id); deleteSession(item.id); onDeleted?.(); },
      },
    ],
  );
}

/** Run a survey's next step (labels.nextStep). */
export function runNextStep(item, step) {
  if (step.kind === 'cancel') cancelUpload(item.id);
  else enqueue(item.id);
}
