/**
 * IFC handoff between Enrich → LCA pages using IndexedDB.
 *
 * sessionStorage has a ~5 MB limit (even lower on some mobile browsers),
 * which enriched IFC files easily exceed.  IndexedDB has no practical
 * size cap, so we use it as the transport and fall back to sessionStorage
 * only for very small payloads.
 */

const DB_NAME = 'lignum-handoff';
const STORE = 'ifc';
const KEY = 'pending';

interface HandoffPayload {
  text: string;
  name: string;
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE);
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

/** Store enriched IFC text for the LCA page to pick up. */
export async function storeHandoff(text: string, name: string): Promise<void> {
  try {
    const db = await openDb();
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).put({ text, name } satisfies HandoffPayload, KEY);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
    db.close();
  } catch {
    // IndexedDB unavailable (e.g. private browsing on old Safari) — try sessionStorage
    sessionStorage.setItem('lca-ifc-text', text);
    sessionStorage.setItem('lca-ifc-name', name);
  }
}

/** Retrieve (and delete) the pending handoff payload, if any. */
export async function consumeHandoff(): Promise<HandoffPayload | null> {
  // Try IndexedDB first
  try {
    const db = await openDb();
    const payload = await new Promise<HandoffPayload | null>((resolve, reject) => {
      const tx = db.transaction(STORE, 'readwrite');
      const store = tx.objectStore(STORE);
      const getReq = store.get(KEY);
      getReq.onsuccess = () => {
        const val = getReq.result as HandoffPayload | undefined;
        if (val) store.delete(KEY);
        resolve(val ?? null);
      };
      getReq.onerror = () => reject(getReq.error);
    });
    db.close();
    if (payload) return payload;
  } catch {
    // fall through to sessionStorage
  }

  // Fallback: sessionStorage
  const text = sessionStorage.getItem('lca-ifc-text');
  const name = sessionStorage.getItem('lca-ifc-name');
  if (text) {
    sessionStorage.removeItem('lca-ifc-text');
    sessionStorage.removeItem('lca-ifc-name');
    return { text, name: name || 'enriched.ifc' };
  }

  return null;
}
