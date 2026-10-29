import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, readdir, stat } from 'node:fs/promises';
import { join } from 'node:path';

const root = new URL('../', import.meta.url);
const read = relative => readFile(new URL(relative, root), 'utf8');

test('build dependencies and scripts are exact and install scripts are disabled', async () => {
  const packageJson = JSON.parse(await read('package.json'));
  assert.deepEqual(packageJson.dependencies, { react: '19.2.0', 'react-dom': '19.2.0' });
  assert.deepEqual(packageJson.devDependencies, {
    '@types/react': '19.2.2',
    '@types/react-dom': '19.2.2',
    typescript: '5.9.3',
    vite: '7.3.7',
  });
  assert.deepEqual(packageJson.overrides, { esbuild: '0.27.2' });
  assert.equal(packageJson.scripts.typecheck, 'tsc --noEmit');
  assert.equal(packageJson.scripts.build, 'tsc --noEmit && vite build');
});

test('lockfile pins every package to registry integrity metadata and the approved override', async () => {
  const lock = JSON.parse(await read('package-lock.json'));
  assert.equal(lock.lockfileVersion, 3);
  assert.equal(lock.packages['node_modules/esbuild'].version, '0.27.2');
  const packages = Object.entries(lock.packages).filter(([path]) => path !== '');
  assert.equal(packages.length, 71);
  for (const [path, metadata] of packages) {
    assert.match(metadata.version, /^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$/,
      `${path} must have an exact version`);
    assert.match(metadata.resolved, /^https:\/\/registry\.npmjs\.org\//,
      `${path} must use the npm registry`);
    assert.match(metadata.integrity, /^sha512-[A-Za-z0-9+/]+={0,2}$/,
      `${path} must have SHA-512 integrity`);
  }
});

test('production bundle is local, hashed, bounded, and has no remote runtime dependencies', async () => {
  const index = await read('dist/index.html');
  assert.match(index, /assets\/index-[A-Za-z0-9_-]+\.js/);
  assert.match(index, /assets\/index-[A-Za-z0-9_-]+\.css/);
  assert.doesNotMatch(index, /https?:|\/\//i);
  const assetDir = new URL('dist/assets/', root);
  const names = (await readdir(assetDir)).sort();
  assert.equal(names.length, 2);
  assert.ok(names.some(name => /^index-[A-Za-z0-9_-]+\.js$/.test(name)));
  assert.ok(names.some(name => /^index-[A-Za-z0-9_-]+\.css$/.test(name)));
  for (const name of names) {
    assert.doesNotMatch(name, /\.map$/);
    const path = join(assetDir.pathname, name);
    assert.ok((await stat(path)).size > 0);
    assert.ok((await stat(path)).size < 4 * 1024 * 1024);
    const bytes = await readFile(path);
    const content = bytes.toString('utf8');
    assert.doesNotMatch(content, /BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|api[_-]?key|secret[_-]?key/i);
    const urls = content.match(/https?:\/\/[^"'`\\\s)]+/g) ?? [];
    assert.ok(urls.every(url => url.startsWith('https://react.dev/errors/') ||
      url.startsWith('http://www.w3.org/')), `unexpected remote URL in ${name}`);
    assert.equal(createHash('sha256').update(bytes).digest('hex').length, 64);
  }
});

test('shipped JavaScript includes the temporary manual demo and unscored status contract', async () => {
  const names = await readdir(new URL('dist/assets/', root));
  const javascript = names.find(name => /^index-[A-Za-z0-9_-]+\.js$/.test(name));
  assert.ok(javascript, 'a generated JavaScript asset must be present');
  const bundle = await read(`dist/assets/${javascript}`);
  for (const required of [
    'Experimental text-only demo',
    'Manually entered demo text',
    'Generate demo candidates',
    'Clear text and remove results',
    'TEMPORARY_UNVALIDATED',
    'Verified score',
    'Experimental score',
  ]) {
    assert.ok(bundle.includes(required), `shipped bundle is missing ${required}`);
  }
});
