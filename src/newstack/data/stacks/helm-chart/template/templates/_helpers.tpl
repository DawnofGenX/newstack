{{/*
Naming helpers. Every template calls these instead of hard-coding a name, so
`nameOverride` and `fullnameOverride` work the way chart consumers expect.
*/}}
{{- define "{{ npm_name }}.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Fully qualified app name: <release>-<chart> unless fullnameOverride is set.
*/}}
{{- define "{{ npm_name }}.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Chart label value: <name>-<version>, with "+" replaced because label values
may not contain it.
*/}}
{{- define "{{ npm_name }}.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels, applied to every object.
*/}}
{{- define "{{ npm_name }}.labels" -}}
helm.sh/chart: {{ include "{{ npm_name }}.chart" . }}
{{ include "{{ npm_name }}.selectorLabels" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels. These must be stable across upgrades - never add a version
here, or a rollout orphans the old pods.
*/}}
{{- define "{{ npm_name }}.selectorLabels" -}}
app.kubernetes.io/name: {{ include "{{ npm_name }}.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
The service account name: explicit override, else the fullname.
*/}}
{{- define "{{ npm_name }}.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "{{ npm_name }}.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
