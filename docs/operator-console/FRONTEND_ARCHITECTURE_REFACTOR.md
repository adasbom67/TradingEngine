# Frontend Architecture Refactor

The operator console has been split from one large App.tsx into focused modules:

- `pages/Dashboard.tsx`
- `pages/Backtesting.tsx`
- `pages/Recommendations.tsx`
- `components/common/Metric.tsx`
- `components/common/RecommendationAtoms.tsx`
- `components/common/ComingSoon.tsx`
- `types/index.ts`
- `utils/format.ts`

This release intentionally preserves existing behavior. It is an architecture-only refactor to reduce release risk before Trade Compare and Portfolio Intelligence.
