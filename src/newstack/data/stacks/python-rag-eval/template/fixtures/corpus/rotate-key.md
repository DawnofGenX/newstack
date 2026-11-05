# Rotating a signing key

Every token this service issues is signed with the key in the active slot. Rotation
is two writes, never one: first publish the new key in slot two so verifiers can
already accept it, then flip the active pointer, and only then retire the old key.
A verifier that only reads the active slot rejects every token minted during the
window between the two writes, which is why the two-slot layout exists at all.

Rotation is safe to repeat. Each key carries a creation timestamp, and a key younger
than the clock skew of the fleet is never retired, so two operators rotating at once
cannot leave the service with no usable key. Token issuers cache the pointer for at
most ten seconds; a rotation therefore takes effect within that window, not
immediately, and the audit log records both writes with the operator id.
