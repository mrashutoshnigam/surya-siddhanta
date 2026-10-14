import { api } from "../../../api";
import { makeProbe } from "../probe";

/** The Chapter 3 probe hooks: `useProbe` (exact answers) and `useLastProbe` (sticky). */
export const { useProbe, useLastProbe } = makeProbe(api.bookChapter3Probe);
