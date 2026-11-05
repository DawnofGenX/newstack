import { Component, computed, signal } from '@angular/core';

import { countText, summarize } from './stats';

@Component({
  imports: [],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  protected readonly title = signal('Text stats');
  protected readonly text = signal('');
  protected readonly counts = computed(() => countText(this.text()));
  protected readonly summary = computed(() => summarize(this.counts()));

  protected update(value: string): void {
    this.text.set(value);
  }

  protected clear(): void {
    this.text.set('');
  }
}
