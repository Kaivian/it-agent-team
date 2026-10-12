# Frontend workflow

Load only for frontend tasks; reuse within the active context. Apply in every mode, including auto: routine implementation choices must be grounded in the project, and auto mode does not authorize inventing missing UI requirements.

## Inspect and clarify

- Inspect the target page, a comparable existing page, component exports/usages, theme tokens and styling configuration. Prefer focused searches and existing stories or examples over reading the entire UI codebase.
- Record concise references to the components and style examples that will guide the change. Do not guess layouts, interactions, labels, data contracts or design values when neither the request nor existing project evidence settles them. Ask the user about unresolved points before implementing the affected behavior, and again whenever new uncertainty arises. Reuse prior answers; there is no fixed question or round limit.
- Match the current site's typography, spacing, color tokens, borders, radii, shadows, icons, layout, responsive breakpoints and interaction states. Use existing conventions for loading, empty, error, disabled, focus and dark-mode states where applicable. Avoid introducing a new visual system or fabricated production data.

## Visual quality and interaction

- Ground visual decisions in the existing site or a user-provided reference. Identify the page's primary task and action; make heading levels, grouping and action emphasis clear. Improve alignment, spacing rhythm, typography hierarchy and content density with existing tokens rather than adding an unrelated aesthetic. Clarify missing design direction before choosing it.
- Preserve readable line lengths and clear labels; avoid competing primary actions, arbitrary decorative gradients, shadows, icons or animation. Use decoration and motion only when supported by the design system and useful to the interaction, respecting reduced-motion behavior.
- Check narrow and wide layouts with realistic long text and relevant empty/loading/error states. Avoid unintended clipping, overflow, layout shifts and inconsistent control sizing. Reuse established loading, retry and validation patterns, with feedback near the action or field.
- Use semantic elements and existing accessible primitives. Check keyboard operation, visible focus, accessible names, contrast and relevant touch-target sizing; do not communicate state only through color. Keep disabled, selected, hover and focus states consistent with the site.
- When preview tools are available, compare the changed UI against its reference at relevant viewports, inspect the result and fix observed issues within scope before final verification. Keep screenshots as evidence when useful. This is visual refinement of the agreed design, not permission to redesign shared pages.

## Component logic and state

- Keep rendering, domain transformations and data access understandable with the project's existing component/hook/service boundaries. Extract a hook or helper for a coherent responsibility, not merely to relocate every few lines.
- Keep state local to its owner unless consumers need shared ownership. Derive display values instead of storing synchronized copies; model mutually exclusive states explicitly. For React tasks, avoid redundant or contradictory state and follow existing update conventions.
- Reuse established data-loading and event patterns. Handle stale responses, cleanup, retry and duplicate submission where relevant; do not add memoization or global state without a demonstrated need. Verify these behaviors alongside appearance.

## Reuse and shared changes

- Search for a suitable existing component before creating one. Prefer its supported props, slots, variants and composition patterns, along with existing class-merging helpers. Create a local component only when existing ones cannot satisfy the clarified requirement; record that reason briefly.
- Default to composing at the target page or using an existing variant. Do not alter shared defaults, global styles, theme configuration or public component contracts merely to customize one consumer.
- If a shared change is necessary, identify consumers through imports, re-exports, wrappers, stories and relevant routes. Describe the affected defaults, props and behavior; obtain ownership of the shared files in the task contract before editing. Clarify intended broader behavior with the user if unresolved; routine authorized edits need no separate approval.
- Prefer additive, opt-in variants that preserve existing defaults and unrelated consumers. Check class merging and precedence so a local override does not accidentally alter shared behavior. Verify affected consumers and representative existing uses, especially responsive and interactive states. If impact cannot be established, pause the shared edit and ask for missing input or report the verification gap.

## Keep inline classes minimal

- Use component defaults and supported variants first. Add classes at the call site only for necessary local layout or behavior that the existing API does not express. Remove redundant utilities and avoid repeating a component's internal styling through overrides. Do not impose an arbitrary class-count limit.
- When the same meaningful style group is used in several places within the task's scope, consolidate it instead of copying more class strings. Repeated markup and behavior belong in a reusable component; visual differences of one component belong in its variant API. For style-only reuse, use a named class constant or style helper consistent with the project. Prefer existing mechanisms and dependencies over introducing another abstraction library.
- Calling `cn` or `clsx` separately around identical literal strings does not consolidate them. Define the shared group once, compose necessary local differences with the existing merger, and keep full Tailwind class strings statically detectable. Check precedence, responsive variants and interactive states after extraction.
- Keep the abstraction near its consumers; make it shared only when reuse warrants it. Avoid global CSS or bulk `@apply` conversion merely to shorten JSX. Use semantic CSS classes only when that is the project's established convention and it preserves the intended Tailwind behavior. Apply shared-file ownership and consumer checks to any extracted shared styling; leave unrelated existing class lists outside task scope.

## Tailwind CSS

- Use Tailwind utilities for new or changed styling, reusing project tokens and conventions. Inspect the installed version, CSS/config entrypoint, plugins and editor settings first. If Tailwind is absent, clarify setup scope before adding it; do not silently migrate existing styles or upgrade Tailwind.
- Prefer supported canonical utilities over equivalent arbitrary values or verbose variants. Apply `tailwindCSS.lint.suggestCanonicalClasses` suggestions only when equivalent under the installed version, theme, root font size and variants. Keep a justified arbitrary value when no equivalent utility exists; do not change intended styling merely to remove a diagnostic.
- Preserve enabled canonical-class diagnostics. When adding project editor configuration within task scope, use `"tailwindCSS.lint.suggestCanonicalClasses": "warning"` or the project's stricter setting; never disable the rule to hide findings. Use available IntelliSense/language-server diagnostics and inspect the changed lines. A normal CSS build or ESLint run does not prove this editor diagnostic ran.
- Keep class names statically detectable, using complete strings or the project's supported source-registration mechanism. Reuse the configured formatter/class sorter; avoid conflicting utilities, broad CSS overrides and unnecessary `!important`.

## Verification and handoff

Run relevant project build, type and lint checks. Review changed call sites for redundant inline classes and repeated style groups, and verify that extraction preserves appearance, class detection and override behavior. Compare the changed UI against the referenced existing page at relevant viewports and states when browser or preview tools are available. For shared edits, include consumer regression checks. Record actual evidence through the runtime; report unavailable visual or canonical-diagnostic checks explicitly rather than claiming they passed.

Return the normal result schema with brief references to reused components, necessary shared changes, checks and unresolved issues. Keep full logs and screenshots in session artifacts.

Sources: [Tailwind CSS IntelliSense canonical diagnostics](https://github.com/tailwindlabs/tailwindcss-intellisense#tailwindcsslintsuggestcanonicalclasses), [Tailwind class detection](https://tailwindcss.com/docs/detecting-classes-in-source-files). Use documentation matching the project's installed version.

Design and state references: [W3C accessible design tips](https://www.w3.org/WAI/tips/designing/), [React state structure](https://react.dev/learn/choosing-the-state-structure). Apply React-specific guidance only to React projects.
