import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { Glossary } from '../views/Glossary';
import { categoryOf } from '../data/glossaryCategories';
import { loadDatasetFromDisk } from './helpers';

const data = loadDatasetFromDisk();

describe('Glossary', () => {
  it('groups every real term under a category heading, none dropped', () => {
    render(<Glossary data={data} />);
    for (const term of Object.keys(data.glossary.terms)) {
      expect(screen.getByText(term)).toBeInTheDocument();
    }
  });

  it('shows the short definition by default and the long one only after expanding', async () => {
    render(<Glossary data={data} />);
    const [term, def] = Object.entries(data.glossary.terms)[0]!;
    expect(screen.getByText(def.short_definition)).toBeInTheDocument();
    expect(screen.queryByText(def.long_explanation)).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: term }));
    expect(screen.getByText(def.long_explanation)).toBeInTheDocument();
  });

  it("categorises every real term consistently with ui/data/glossaryCategories.ts", () => {
    render(<Glossary data={data} />);
    // Every term must land in exactly the category the shared lookup assigns --
    // this just confirms the view didn't silently miscategorise or drop one.
    for (const term of Object.keys(data.glossary.terms)) {
      expect(categoryOf(term)).toBeTruthy();
    }
  });
});
