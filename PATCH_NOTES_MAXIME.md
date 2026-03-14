# Patch RTE Tempo – pilotage et observabilité résilience

Contenu du patch livré :

- correction et fiabilisation de `resilience_service.py`
- ajout d'un sélecteur runtime non destructif :
  - `select.rte_tempo_selecteur_source_tempo`
- ajout d'un bouton reset résilience :
  - `button.rte_tempo_reset_resilience_tempo`
- ajout de capteurs de diagnostic :
  - `sensor.rte_tempo_mode_source_tempo`
  - `sensor.rte_tempo_coherence_tempo`
  - `sensor.rte_tempo_tempo_derniere_mise_a_jour_resilience`
- ajout d'un binaire de santé :
  - `binary_sensor.rte_tempo_tempo_degrade`
- enrichissement des attributs sur les capteurs résolus aujourd'hui / demain
- support d'un mode forcé `default`
- amélioration du parsing des valeurs locales texte (bleu/blanc/rouge, HCJB/HCJW/HCJR, etc.)
- amélioration de l'options flow pour mieux exposer les champs résilience

## Entités de test à attendre après redémarrage

- Couleur résolue aujourd'hui
- Source résolue aujourd'hui
- Couleur résolue demain
- Source résolue demain
- Mode source Tempo
- Cohérence Tempo
- Tempo dernière mise à jour résilience
- Tempo dégradé
- Sélecteur source Tempo
- Reset résilience Tempo

## Comment connecter vos deux infos locales

Dans l'intégration :

Paramètres > Appareils & services > RTE Tempo > Configurer

Renseigner :

- `local_today_entity`
- `local_tomorrow_entity`

Exemple attendu :

- `sensor.knx_tempo_today`
- `sensor.knx_tempo_tomorrow`

## Sémantique du sélecteur

- `auto` : RTE puis local puis fallback
- `web` : force RTE
- `local` : force la source locale HA
- `default` : force la valeur par défaut configurée

Le bouton reset :

- vide le cache `last_good_*`
- supprime le mode forcé runtime
- revient à la configuration sauvegardée
