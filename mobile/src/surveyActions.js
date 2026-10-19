// What the survey list and the survey screen both do to a survey.
import { Alert } from 'react-native';
import { reprocessVideo } from './api';
import { checkNow } from './serverStatus';
import { deleteSession, updateSession } from './storage';
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

/**
 * Testing: analyse an uploaded survey again on the server with the current model and settings.
 * Its damage records on the web app are replaced, so a finished survey asks first.
 */
export function confirmReanalyse(item) {
  const run = () => runNextStep(item, { kind: 'reanalyse' });
  if (item.serverStatus === 'failed') return run();
  const n = item.serverDetections;
  Alert.alert(
    'Analyse it again?',
    `The server analyses the video again with its current model and settings. The ${n != null ? `${n} ` : ''}damage records it found are replaced, and any inspection status set on them is lost. Nothing is uploaded.`,
    [{ text: 'Keep them', style: 'cancel' }, { text: 'Analyse again', style: 'destructive', onPress: run }],
  );
  return undefined;
}

/** Testing: send the phone's copy again. The web app gets a second survey; the first one stays. */
export function confirmReupload(item) {
  Alert.alert(
    'Upload it again?',
    'The video and GPS track are sent again and analysed as a new survey. The survey already on the web app stays, so delete it there if you do not need both.',
    [{ text: 'Cancel', style: 'cancel' }, { text: 'Upload again', onPress: () => enqueue(item.id) }],
  );
}

/** Run a survey's next step (labels.nextStep). */
export async function runNextStep(item, step) {
  if (step.kind === 'cancel') return cancelUpload(item.id);
  if (step.kind !== 'reanalyse') return enqueue(item.id);

  try {
    const video = await reprocessVideo(item.serverVideoId);
    if (!video) {
      // The server no longer has this survey or its video: send the phone's copy again.
      Alert.alert('Uploading it again', 'The web app no longer has this survey, so the video on this phone is being sent again.');
      enqueue(item.id);
      return undefined;
    }
    updateSession(item.id, { serverStatus: video.status, serverProgress: 0, serverDetections: null, serverError: null });
    checkNow();
  } catch (e) {
    if (e.status !== 401) Alert.alert('Could not analyse it again', e.message);
  }
  return undefined;
}
