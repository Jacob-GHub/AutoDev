// First path segments on github.com that are not repositories.
const NON_REPO_ROOTS = new Set([
  'settings', 'notifications', 'explore', 'marketplace', 'pulls', 'issues',
  'orgs', 'organizations', 'login', 'logout', 'signup', 'sponsors', 'topics',
  'trending', 'codespaces', 'new', 'features', 'about', 'search', 'collections',
  'dashboard', 'enterprise', 'pricing', 'security', 'site',
])

/** The current page's repository URL, or null when not on a repo page. */
export function getRepoUrl(pathname = window.location.pathname): string | null {
  const match = pathname.match(/^\/([^/]+)\/([^/]+)/)
  if (!match || NON_REPO_ROOTS.has(match[1].toLowerCase())) return null
  return `https://github.com/${match[1]}/${match[2]}`
}
