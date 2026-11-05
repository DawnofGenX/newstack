import { TestBed } from '@angular/core/testing';

import { App } from './app';

async function render() {
  await TestBed.configureTestingModule({ imports: [App] }).compileComponents();
  const fixture = TestBed.createComponent(App);
  await fixture.whenStable();
  return fixture;
}

describe('App', () => {
  it('renders the title', async () => {
    const fixture = await render();
    const heading = (fixture.nativeElement as HTMLElement).querySelector('h1');
    expect(heading?.textContent).toContain('Text stats');
  });

  it('starts empty', async () => {
    const fixture = await render();
    const element = fixture.nativeElement as HTMLElement;
    expect(element.querySelector('[data-testid="summary"]')?.textContent).toContain('0 lines');
  });

  it('recounts when the textarea changes', async () => {
    const fixture = await render();
    const element = fixture.nativeElement as HTMLElement;
    const textarea = element.querySelector('[data-testid="input"]') as HTMLTextAreaElement;

    textarea.value = 'a b\nc\n';
    textarea.dispatchEvent(new Event('input'));
    await fixture.whenStable();

    expect(element.querySelector('[data-testid="lines"]')?.textContent?.trim()).toBe('2');
    expect(element.querySelector('[data-testid="words"]')?.textContent?.trim()).toBe('3');
    expect(element.querySelector('[data-testid="bytes"]')?.textContent?.trim()).toBe('6');
  });

  it('clears with the button', async () => {
    const fixture = await render();
    const element = fixture.nativeElement as HTMLElement;
    const textarea = element.querySelector('[data-testid="input"]') as HTMLTextAreaElement;
    textarea.value = 'hello';
    textarea.dispatchEvent(new Event('input'));
    await fixture.whenStable();

    (element.querySelector('button') as HTMLButtonElement).click();
    await fixture.whenStable();

    expect(element.querySelector('[data-testid="bytes"]')?.textContent?.trim()).toBe('0');
  });
});
