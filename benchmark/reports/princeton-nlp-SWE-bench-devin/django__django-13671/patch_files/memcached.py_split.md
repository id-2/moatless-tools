

## EpicSplitter

9 chunks

#### Split 1
239 tokens, line: 1 - 40

```python
"Memcached cache backend"

import pickle
import re
import time
import warnings

from django.core.cache.backends.base import (
    DEFAULT_TIMEOUT, BaseCache, InvalidCacheKey, memcache_key_warnings,
)
from django.utils.deprecation import RemovedInDjango41Warning
from django.utils.functional import cached_property


class BaseMemcachedCache(BaseCache):
    def __init__(self, server, params, library, value_not_found_exception):
        super().__init__(params)
        if isinstance(server, str):
            self._servers = re.split('[;,]', server)
        else:
            self._servers = server

        # Exception type raised by the underlying client library for a
        # nonexistent key.
        self.LibraryValueNotFoundException = value_not_found_exception

        self._lib = library
        self._class = library.Client
        self._options = params.get('OPTIONS') or {}

    @property
    def client_servers(self):
        return self._servers

    @cached_property
    def _cache(self):
        """
        Implement transparent thread-safe access to a memcached client.
        """
        return self._class(self.client_servers, **self._options)
```



#### Split 2
283 tokens, line: 42 - 67

```python
class BaseMemcachedCache(BaseCache):

    def get_backend_timeout(self, timeout=DEFAULT_TIMEOUT):
        """
        Memcached deals with long (> 30 days) timeouts in a special
        way. Call this function to obtain a safe value for your timeout.
        """
        if timeout == DEFAULT_TIMEOUT:
            timeout = self.default_timeout

        if timeout is None:
            # Using 0 in memcache sets a non-expiring timeout.
            return 0
        elif int(timeout) == 0:
            # Other cache backends treat 0 as set-and-expire. To achieve this
            # in memcache backends, a negative timeout must be passed.
            timeout = -1

        if timeout > 2592000:  # 60*60*24*30, 30 days
            # See https://github.com/memcached/memcached/wiki/Programming#expiration
            # "Expiration times can be set from 0, meaning "never expire", to
            # 30 days. Any time higher than 30 days is interpreted as a Unix
            # timestamp date. If you want to expire an object on January 1st of
            # next year, this is how you do that."
            #
            # This means that we have to switch to absolute timestamps.
            timeout += int(time.time())
        return int(timeout)
```



#### Split 3
370 tokens, line: 69 - 105

```python
class BaseMemcachedCache(BaseCache):

    def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        return self._cache.add(key, value, self.get_backend_timeout(timeout))

    def get(self, key, default=None, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        return self._cache.get(key, default)

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        if not self._cache.set(key, value, self.get_backend_timeout(timeout)):
            # make sure the key doesn't keep its old value in case of failure to set (memcached's 1MB limit)
            self._cache.delete(key)

    def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        return bool(self._cache.touch(key, self.get_backend_timeout(timeout)))

    def delete(self, key, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        return bool(self._cache.delete(key))

    def get_many(self, keys, version=None):
        key_map = {self.make_key(key, version=version): key for key in keys}
        for key in key_map:
            self.validate_key(key)
        ret = self._cache.get_multi(key_map.keys())
        return {key_map[k]: v for k, v in ret.items()}

    def close(self, **kwargs):
        # Many clients don't clean up connections properly.
        self._cache.disconnect_all()
```



#### Split 4
147 tokens, line: 107 - 122

```python
class BaseMemcachedCache(BaseCache):

    def incr(self, key, delta=1, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        # memcached doesn't support a negative delta
        if delta < 0:
            return self._cache.decr(key, -delta)
        try:
            val = self._cache.incr(key, delta)

        # Normalize an exception raised by the underlying client library to
        # ValueError in the event of a nonexistent key when calling incr().
        except self.LibraryValueNotFoundException:
            val = None
        if val is None:
            raise ValueError("Key '%s' not found" % key)
        return val
```



#### Split 5
149 tokens, line: 124 - 139

```python
class BaseMemcachedCache(BaseCache):

    def decr(self, key, delta=1, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        # memcached doesn't support a negative delta
        if delta < 0:
            return self._cache.incr(key, -delta)
        try:
            val = self._cache.decr(key, delta)

        # Normalize an exception raised by the underlying client library to
        # ValueError in the event of a nonexistent key when calling decr().
        except self.LibraryValueNotFoundException:
            val = None
        if val is None:
            raise ValueError("Key '%s' not found" % key)
        return val
```



#### Split 6
203 tokens, line: 141 - 163

```python
class BaseMemcachedCache(BaseCache):

    def set_many(self, data, timeout=DEFAULT_TIMEOUT, version=None):
        safe_data = {}
        original_keys = {}
        for key, value in data.items():
            safe_key = self.make_key(key, version=version)
            self.validate_key(safe_key)
            safe_data[safe_key] = value
            original_keys[safe_key] = key
        failed_keys = self._cache.set_multi(safe_data, self.get_backend_timeout(timeout))
        return [original_keys[k] for k in failed_keys]

    def delete_many(self, keys, version=None):
        keys = [self.make_key(key, version=version) for key in keys]
        for key in keys:
            self.validate_key(key)
        self._cache.delete_multi(keys)

    def clear(self):
        self._cache.flush_all()

    def validate_key(self, key):
        for warning in memcache_key_warnings(key):
            raise InvalidCacheKey(warning)
```



#### Split 7
361 tokens, line: 166 - 197

```python
class MemcachedCache(BaseMemcachedCache):
    "An implementation of a cache binding using python-memcached"
    def __init__(self, server, params):
        warnings.warn(
            'MemcachedCache is deprecated in favor of PyMemcacheCache and '
            'PyLibMCCache.',
            RemovedInDjango41Warning, stacklevel=2,
        )
        # python-memcached ≥ 1.45 returns None for a nonexistent key in
        # incr/decr(), python-memcached < 1.45 raises ValueError.
        import memcache
        super().__init__(server, params, library=memcache, value_not_found_exception=ValueError)
        self._options = {'pickleProtocol': pickle.HIGHEST_PROTOCOL, **self._options}

    def get(self, key, default=None, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        val = self._cache.get(key)
        # python-memcached doesn't support default values in get().
        # https://github.com/linsomniac/python-memcached/issues/159
        # Remove this method if that issue is fixed.
        if val is None:
            return default
        return val

    def delete(self, key, version=None):
        # python-memcached's delete() returns True when key doesn't exist.
        # https://github.com/linsomniac/python-memcached/issues/170
        # Call _deletetouch() without the NOT_FOUND in expected results.
        key = self.make_key(key, version=version)
        self.validate_key(key)
        return bool(self._cache._deletetouch([b'DELETED'], 'delete', key))
```



#### Split 8
211 tokens, line: 200 - 223

```python
class PyLibMCCache(BaseMemcachedCache):
    "An implementation of a cache binding using pylibmc"
    def __init__(self, server, params):
        import pylibmc
        super().__init__(server, params, library=pylibmc, value_not_found_exception=pylibmc.NotFound)

    @property
    def client_servers(self):
        output = []
        for server in self._servers:
            output.append(server[5:] if server.startswith('unix:') else server)
        return output

    def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_key(key, version=version)
        self.validate_key(key)
        if timeout == 0:
            return self._cache.delete(key)
        return self._cache.touch(key, self.get_backend_timeout(timeout))

    def close(self, **kwargs):
        # libmemcached manages its own connections. Don't call disconnect_all()
        # as it resets the failover state and creates unnecessary reconnects.
        pass
```



#### Split 9
120 tokens, line: 226 - 238

```python
class PyMemcacheCache(BaseMemcachedCache):
    """An implementation of a cache binding using pymemcache."""
    def __init__(self, server, params):
        import pymemcache.serde
        super().__init__(server, params, library=pymemcache, value_not_found_exception=KeyError)
        self._class = self._lib.HashClient
        self._options = {
            'allow_unicode_keys': True,
            'default_noreply': False,
            'serde': pymemcache.serde.pickle_serde,
            **self._options,
        }
```
