/** Adevărat dacă utilizatorul scrie într-un câmp sau e deschisă o fereastră: scurtăturile tac. */
export function isTyping(target: EventTarget | null): boolean {
  if (document.querySelector('[role="dialog"]')) return true;
  if (!(target instanceof HTMLElement)) return false;
  return target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName);
}
