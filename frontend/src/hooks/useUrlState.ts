'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { objectEntries, objectFromEntries, objectKeys } from '../utils/typedObjectHelpers';

type TransformConfig<T> = {
  fromUrl?: (value: string) => T;
  toUrl?: (value: T) => string;
  defaultValue: T;
};

type TypedTransformConfig<T> = { [K in keyof T]: TransformConfig<T[K]> };
type State<T> = { [K in keyof T]: T[K] };

export function useUrlStateGroup<T extends object>(transforms: TypedTransformConfig<T>) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const keys = useMemo(() => objectKeys(transforms), [transforms]);

  // helper to build state from current URL
  const parseFromUrl = useCallback((): State<T> => {
    const map = new Map<keyof T, T[keyof T]>();
    for (const key of keys) {
      const cfg = transforms[key];
      const raw = searchParams?.get(String(key));
      const val =
        raw != null ? (cfg.fromUrl?.(raw) ?? cfg.defaultValue) : cfg.defaultValue;
      map.set(key, val);
    }
    return objectFromEntries<T>(map);
  }, [keys, transforms, searchParams]);

  // initialize from URL
  const [state, setState] = useState<State<T>>(() => parseFromUrl());

  // keep state in sync if URL changes via back/forward or external nav
  const lastSearch = useRef<string | null>(null);
  useEffect(() => {
    const current = searchParams?.toString() ?? '';
    if (current !== lastSearch.current) {
      lastSearch.current = current;
      setState(parseFromUrl());
    }
  }, [parseFromUrl, searchParams]);

  // queue a nav (to avoid pushing during render)
  const [nextHref, setNextHref] = useState<string | null>(null);
  useEffect(() => {
    if (!nextHref) return;
    router.push(nextHref);
    setNextHref(null);
  }, [nextHref, router]);

  // Update URL + state
  const updateQuery = useCallback(
    (updates: Partial<State<T>>) => {
      const currentParams = new URLSearchParams(searchParams?.toString());
      const nextState = { ...state };

      let urlChanged = false;

      objectEntries(updates).forEach(([key, value]) => {
        const cfg = transforms[key];

        if (value == null || value === '') {
          // remove from URL, reset state to default
          if (currentParams.has(String(key))) {
            currentParams.delete(String(key));
            urlChanged = true;
          }
          nextState[key] = cfg.defaultValue;
        } else {
          const urlValue = cfg.toUrl ? cfg.toUrl(value) : String(value);
          const prev = currentParams.get(String(key));
          if (prev !== urlValue) {
            currentParams.set(String(key), urlValue);
            urlChanged = true;
          }
          nextState[key] = value;
        }
      });

      setState(nextState);

      if (urlChanged) {
        const search = currentParams.toString();
        const href = search ? `${pathname}?${search}` : `${pathname}`;
        setNextHref(href); // push later (effect), not during render
      }
    },
    [pathname, searchParams, state, transforms]
  );

  return { query: state, updateQuery };
}
