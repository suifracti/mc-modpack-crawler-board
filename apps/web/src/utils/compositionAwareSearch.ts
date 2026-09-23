export function bindCompositionAwareSearchInput(
  input: HTMLInputElement,
  updateValue: (value: string) => void,
  commit: () => void,
): void {
  let composing = false;
  let lastCommittedValue = input.value;

  const publish = (shouldCommit: boolean): void => {
    const value = input.value;
    updateValue(value);
    if (!shouldCommit || value === lastCommittedValue) return;
    lastCommittedValue = value;
    commit();
  };

  input.addEventListener('compositionstart', () => {
    composing = true;
  });
  input.addEventListener('compositionend', () => {
    composing = false;
    publish(true);
  });
  input.addEventListener('input', (event) => {
    const isComposing = composing || (event as InputEvent).isComposing === true;
    publish(!isComposing);
  });
}
