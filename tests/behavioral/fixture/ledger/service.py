RENDERERS = {}


def _obsolete_label(label):
    return f"[{label}]"


def public_export(label):
    return f"export:{label}"


def read_snapshot(snapshot):
    if snapshot["version"] == 1:
        return snapshot["name"]
    if snapshot["version"] == 2:
        return snapshot["label"]
    raise ValueError("unsupported snapshot version")


def restore_snapshot(user, allowed_ledgers, target, snapshot, write):
    if user["role"] != "operator":
        raise PermissionError("operator role required")
    if target not in allowed_ledgers:
        raise PermissionError("target outside ledger scope")
    label = read_snapshot(snapshot)
    try:
        write(target, label)
    except TimeoutError:
        write(target, label)


def import_csv_row(label):
    label = label.strip()
    if not label:
        raise ValueError("empty label")
    return label


def import_text_row(label):
    label = label.strip()
    if not label:
        raise ValueError("empty label")
    return label
