import { useCallback, useRef, useState } from 'react';

const OFFSET_X = 16;
const OFFSET_Y = 16;

/**
 * Fare bir öğenin üzerine geldiğinde, farenin bulunduğu konumda o öğeye ait
 * notu gösteren küçük bir tooltip için gereken state ve event handler'ları
 * sağlayan hook. Notlar çok uzun olabileceği için tooltip içeriği
 * max-height + overflow-y ile sınırlandırılır (bkz. NoteTooltip bileşeni).
 */
function useNoteTooltip() {
  const [tooltip, setTooltip] = useState(null); // { note, x, y }
  const frameRef = useRef(null);

  const showTooltip = useCallback((note) => (e) => {
    if (!note) return;
    const { clientX, clientY } = e;
    setTooltip({ note, x: clientX, y: clientY });
  }, []);

  const moveTooltip = useCallback((e) => {
    const { clientX, clientY } = e;
    if (frameRef.current) cancelAnimationFrame(frameRef.current);
    frameRef.current = requestAnimationFrame(() => {
      setTooltip((prev) => (prev ? { ...prev, x: clientX, y: clientY } : prev));
    });
  }, []);

  const hideTooltip = useCallback(() => {
    setTooltip(null);
  }, []);

  return { tooltip, showTooltip, moveTooltip, hideTooltip, OFFSET_X, OFFSET_Y };
}

export default useNoteTooltip;
