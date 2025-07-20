import tomlkit
import logging

with open("config.toml", "r") as f:
    config = tomlkit.parse(f.read())


