import { describe, expect, it } from 'vitest';
import { bindCompositionAwareSearchInput } from '../src/utils/compositionAwareSearch';

class OfflineInputNode extends EventTarget {
  value = '';
}

function dispatchInput(input: OfflineInputNode, value: string, isComposing = false): void {
  input.value = value;
  const event = new Event('input');
  Object.defineProperty(event, 'isComposing', { value: isComposing });
  input.dispatchEvent(event);
}

describe('composition-aware search input', () => {
  it('keeps the input node during IME composition, then commits the final text and handles ordinary edits and clearing', () => {
    let currentInput = new OfflineInputNode();
    let searchValue = '';
    const committedValues: string[] = [];

    const mountSearchInput = (): void => {
      const input = currentInput;
      bindCompositionAwareSearchInput(input as HTMLInputElement, (value) => {
        searchValue = value;
      }, () => {
        committedValues.push(searchValue);
        currentInput = new OfflineInputNode();
        currentInput.value = searchValue;
        mountSearchInput();
      });
    };

    mountSearchInput();
    const composingNode = currentInput;
    composingNode.dispatchEvent(new Event('compositionstart'));
    dispatchInput(composingNode, 'ji', true);

    expect(currentInput).toBe(composingNode);
    expect(searchValue).toBe('ji');
    expect(committedValues).toEqual([]);

    composingNode.value = '机械动力';
    composingNode.dispatchEvent(new Event('compositionend'));
    expect(currentInput).not.toBe(composingNode);
    expect(searchValue).toBe('机械动力');
    expect(committedValues).toEqual(['机械动力']);

    const ordinaryInput = currentInput;
    dispatchInput(ordinaryInput, '魔法模组');
    expect(currentInput).not.toBe(ordinaryInput);
    expect(searchValue).toBe('魔法模组');
    expect(committedValues).toEqual(['机械动力', '魔法模组']);

    const clearingInput = currentInput;
    dispatchInput(clearingInput, '');
    expect(currentInput).not.toBe(clearingInput);
    expect(searchValue).toBe('');
    expect(committedValues).toEqual(['机械动力', '魔法模组', '']);
  });
});
