# Pxsol simple storage

A simple data storage contract that allows anyone to store data on the chain.

- Users can only store data in their own data accounts.
- Developed by [pxsol](https://github.com/mohanson/pxsol).

Deployed on the local test chain:

```sh
$ cargo build-sbf
$ python make.py deploy
# 2025/05/20 16:06:38 main: deploy program pubkey="T6vZUAQyiFfX6968XoJVmXxpbZwtnKfQbNNBYrcxkcp"
```

```sh
# Save some data.
$ python make.py save "The quick brown fox jumps over the lazy dog"

# Load data.
$ python make.py load
# The quick brown fox jumps over the lazy dog.

# Save some data and overwrite the old data.
$ python make.py save "片云天共远, 永夜月同孤."
# Load data.
$ python make.py load
# 片云天共远, 永夜月同孤.
```

# License

MIT.
