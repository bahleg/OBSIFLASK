## 🥸 Obfuscation

OBSIFLASK supports basic obfuscation for text and binary documents.  
The text obfuscation uses a repeating-key XOR, which is **not** cryptographically secure — **do not** rely on it to protect sensitive notes. Use it only for light obfuscation. Its main advantage is that it’s **git-friendly**: small edits to a document produce only small changes in the encoded file, so diffs remain useful. This makes it handy when you want to avoid storing plain text in a Git repository.

To obfuscate a document, give it the `.obf` extension (see the example document). You can also use a command `obsiflask-deobfuscate` to de-obfuscate the documents outside the OBSIFLASK.

The obfuscation functionality requires a key. It can be set for each vault using `obfuscation_key` in the [config](https://github.com/bahleg/OBSIFLASK/blob/main/obsiflask/config.py). By default its vaule is `abc`.

Check an example of the obfuscated note [[obfuscated.obf.md| here]] (won't work under Obsidian).

## 🔐 Encryption

**OBSIFLASK** provides partial support for encryption compatible with the [Meld Encrypt Obsidian plugin](https://github.com/meld-cp/obsidian-encrypt)

You can **encrypt and decrypt inline text** in Markdown nodes, as well as decrypt fully encrypted `.mdenc` files.  
(Full-file encryption and re-encryption are not supported yet.)

Check an example of the note with an encrypted inline content  [[inline_encryption.md| here]] and an example of the fully encrypted note [[example_folder/full_encryption.mdenc| here]] (the password is `abc`).

To decrypt content without running OBSIFLASK itself, you can use the CLI tool `obsiflask-decrypt`.

⚠️ **Please use encryption at your own risk.**
OBSIFLASK does not guarantee data recovery in case of lost passwords or file corruption. It also uses [the reverse engineered code](https://gist.github.com/mclang/4c3347d217ae6f542e309eb2a0184025) for decryption, not the official one.


## 🧩 Obfuscation vs. Encryption

In addition to Meld-compatible encryption, **OBSIFLASK** also supports a lightweight **text obfuscation** mode.  
Both methods serve to hide content, but they differ in purpose, compatibility, and strength.

| Feature                    | **Obfuscation (OBSIFLASK)**                            | **Meld Encryption**                                                |
| -------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------ |
| **Compatibility**          | Works **only in OBSIFLASK**                            | Works in **both Obsidian and OBSIFLASK**                           |
| **Cryptographic strength** | Very weak (simple reversible transformation)           | Moderate to strong (depends on password and plugin configuration)  |
| **Git-friendliness**       | Small text changes produce small diffs in encoded form | Even minor edits cause large binary-like diffs                     |
| **Purpose**                | Superficial content hiding                             | Real encryption for confidentiality                                |
| **Decoding location**      | Server-side (handled by OBSIFLASK)                     | Client-side (handled by Obsidian plugin or OBSIFLASK) |
| **Usage warning**          | Suitable only for lightweight protection               | Use at your own risk, but secure enough for typical use cases      |
