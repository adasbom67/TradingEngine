import type { Page } from "../../types";

export function ComingSoon({ page }: { page: Page }) {
  return (
    <article className="card empty-result">
      <h2>{page}</h2>
      <p>
        This workspace is intentionally disabled until its controlled
        implementation slice.
      </p>
    </article>
  );
}
