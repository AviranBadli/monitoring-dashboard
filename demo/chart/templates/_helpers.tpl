{{- define "kueue-dashboard.fullname" -}}
{{- if contains .Chart.Name .Release.Name }}
{{- .Release.Name }}
{{- else }}
{{- .Release.Name }}-{{ .Chart.Name }}
{{- end }}
{{- end }}

{{- define "kueue-dashboard.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "kueue-dashboard.selectorLabels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "kueue-dashboard.serviceAccountName" -}}
{{- if .Values.serviceAccount.name }}
{{- .Values.serviceAccount.name }}
{{- else }}
{{- include "kueue-dashboard.fullname" . }}
{{- end }}
{{- end }}
