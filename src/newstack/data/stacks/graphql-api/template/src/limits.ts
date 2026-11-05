import { GraphQLError, visit, type DocumentNode } from "graphql";

/**
 * How deep a query nests is a cost the client chooses, so the server caps it before the
 * query is executed. Each selection set is one level; `{ stats(text: "x") { bytes } }` is 2.
 *
 * The count is per document, so a fragment's own selections are counted from the fragment
 * definition rather than from the spread site. That can under-count a hand-written deep
 * fragment, which is why the limit is a guard against runaway queries, not a query budget:
 * pair it with a real complexity analysis if you need one.
 */
export function depthOf(document: DocumentNode): number {
  let depth = 0;
  let current = 0;

  visit(document, {
    SelectionSet: {
      enter() {
        current += 1;
        depth = Math.max(depth, current);
      },
      leave() {
        current -= 1;
      },
    },
  });

  return depth;
}

export const MAX_QUERY_DEPTH = 6;

export function depthLimit(maxDepth: number = MAX_QUERY_DEPTH) {
  return {
    onValidate({ addValidationRule }: { addValidationRule: (rule: unknown) => void }) {
      addValidationRule((context: { reportError: (error: GraphQLError) => void }) => ({
        Document: {
          leave(node: DocumentNode) {
            const depth = depthOf(node);
            if (depth > maxDepth) {
              context.reportError(
                new GraphQLError(
                  `query is ${depth} selections deep, the limit is ${maxDepth}`,
                  { extensions: { code: "QUERY_TOO_DEEP" } },
                ),
              );
            }
          },
        },
      }));
    },
  };
}
