const resources = (() => {
    const cache = new Map();

    function load(urls) {
        const list = Array.isArray(urls) ? urls : [urls];

        return Promise.all(list.map(loadOne));
    }

    function loadOne(url) {
        if (cache.has(url)) {
            return cache.get(url);
        }

        const promise = new Promise((resolve, reject) => {
            const image = new Image();

            image.onload = () => {
                resolve(image);
            };

            image.onerror = () => {
                reject(new Error(`Failed to load resource: ${url}`));
            };

            image.src = url;
        });

        cache.set(url, promise);

        return promise;
    }

    function get(url) {
        return cache.get(url);
    }

    function has(url) {
        return cache.has(url);
    }

    function remove(url) {
        cache.delete(url);
    }

    function clear() {
        cache.clear();
    }

    function size() {
        return cache.size;
    }

    return {
        load,
        get,
        has,
        remove,
        clear,
        size
    };
})();

export default resources;
