export function hasPermission(userPermissions: string[], required: string): boolean {
  if (userPermissions.includes(required)) return true;

  const requiredParts = required.split(":");

  for (const granted of userPermissions) {
    if (granted === "*") return true;

    const grantedParts = granted.split(":");

    if (grantedParts.length === requiredParts.length) {
      let matches = true;
      for (let i = 0; i < grantedParts.length; i += 1) {
        if (grantedParts[i] !== "*" && grantedParts[i] !== requiredParts[i]) {
          matches = false;
          break;
        }
      }
      if (matches) return true;
    }

    if (
      grantedParts.length < requiredParts.length &&
      grantedParts[grantedParts.length - 1] === "*"
    ) {
      const grantedPrefix = grantedParts.slice(0, grantedParts.length - 1).join(":");
      const requiredPrefix = requiredParts.slice(0, grantedParts.length - 1).join(":");
      if (grantedPrefix === requiredPrefix) return true;
    }
  }

  return false;
}
