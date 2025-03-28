{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "ran-5g.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "ran-5g.labels" -}}
helm.sh/chart: {{ include "ran-5g.chart" . }}
{{ include "ran-5g.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "ran-5g.selectorLabels" -}}
app.kubernetes.io/name: srs
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
