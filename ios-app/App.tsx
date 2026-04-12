import { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TextInput, TouchableOpacity, ScrollView, Alert, Platform, Modal, Linking } from 'react-native';
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import * as Clipboard from 'expo-clipboard';

// Remplacez cette IP par l'adresse IP locale de votre ordinateur (ex: 192.168.1.x)
const SERVER_URL = 'https://universal-video-audio-downloader.onrender.com'; 

export default function App() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [mediaData, setMediaData] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [loadingText, setLoadingText] = useState('Analyse...');
  
  const [downloading, setDownloading] = useState(false);
  const [progress, setProgress] = useState<any>(null);

  // Cookie management
  const [showCookieModal, setShowCookieModal] = useState(false);
  const [cookieText, setCookieText] = useState('');
  const [hasCookies, setHasCookies] = useState(false);
  const [cookieLoading, setCookieLoading] = useState(false);

  // Check cookie status on mount
  useEffect(() => {
    checkCookieStatus();
  }, []);

  const checkCookieStatus = async () => {
    try {
      const res = await fetch(`${SERVER_URL}/api/cookies/status`);
      const data = await res.json();
      setHasCookies(data.has_cookies);
    } catch (e) {
      // Server might be cold, ignore
    }
  };

  const uploadCookies = async () => {
    if (!cookieText.trim()) {
      setErrorMsg('Collez le contenu de votre fichier cookies.txt');
      return;
    }
    setCookieLoading(true);
    try {
      const res = await fetch(`${SERVER_URL}/api/cookies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cookies_text: cookieText })
      });
      const data = await res.json();
      if (data.success) {
        setHasCookies(true);
        setShowCookieModal(false);
        setCookieText('');
        setErrorMsg('');
      } else {
        setErrorMsg(data.detail || 'Erreur lors de l\'envoi des cookies');
      }
    } catch (e: any) {
      setErrorMsg(e.message);
    } finally {
      setCookieLoading(false);
    }
  };

  const deleteCookies = async () => {
    try {
      await fetch(`${SERVER_URL}/api/cookies`, { method: 'DELETE' });
      setHasCookies(false);
      setShowCookieModal(false);
    } catch (e: any) {
      setErrorMsg(e.message);
    }
  };

  const analyzeUrl = async (customUrl?: string) => {
    const urlToUse = typeof customUrl === 'string' ? customUrl : url;
    setErrorMsg('');
    if (!urlToUse || urlToUse.trim() === '') {
      setErrorMsg('Veuillez coller un lien avant d\'analyser.');
      return;
    }
    setLoading(true);
    setMediaData(null);
    setLoadingText('Analyse...');
    
    // Si c'est la toute première requête, le serveur Cloud (Render) peut mettre 50s à s'allumer
    const timeoutMsgId = setTimeout(() => {
       setLoadingText('Le serveur démarre (jusqu\'à 50s)...');
    }, 5000);

    try {
      const res = await fetch(`${SERVER_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: urlToUse })
      });
      clearTimeout(timeoutMsgId);
      const data = await res.json();
      if (data.success) {
        setMediaData(data);
      } else {
        const detail = data.detail || '';
        // Detect YouTube bot error and show helpful message
        if (detail.includes('Sign in to confirm') || detail.includes('not a bot')) {
          setErrorMsg(
            'YouTube bloque cette requête. Cliquez sur "⚙️ Cookies YouTube" ci-dessous pour configurer vos cookies et débloquer les téléchargements.'
          );
        } else {
          setErrorMsg(detail || 'Erreur lors de l\'analyse');
        }
      }
    } catch (e: any) {
      clearTimeout(timeoutMsgId);
      setErrorMsg(`Impossible de contacter le serveur. S'il était éteint, il démarre peut-être. Patientez 1 min et réessayez !\n(${e.message})`);
    } finally {
      setLoading(false);
    }
  };

  const pasteAndAnalyze = async () => {
    setErrorMsg('');
    const text = await Clipboard.getStringAsync();
    if (text) {
      setUrl(text);
      await analyzeUrl(text);
    } else {
      setErrorMsg("Aucun texte trouvé dans le presse-papier.");
    }
  };

  const startDownload = async (formatItem: any, isAudio: boolean) => {
    setErrorMsg('');
    setDownloading(true);
    setProgress({ percent: 0, status: 'Démarrage du téléchargement...' });
    try {
      const res = await fetch(`${SERVER_URL}/api/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          format_item: formatItem,
          raw_formats: mediaData.raw_formats,
          is_audio_only: isAudio,
          audio_format: 'mp3',
          audio_bitrate: '192'
        })
      });
      const data = await res.json();
      if (data.job_id) {
        connectWebsocket(data.job_id, isAudio ? 'mp3' : formatItem.ext || 'mp4');
      } else {
        setErrorMsg('Impossible de démarrer le téléchargement');
        setDownloading(false);
      }
    } catch (e: any) {
      setErrorMsg(e.message);
      setDownloading(false);
    }
  };

  const connectWebsocket = (jobId: string, ext: string) => {
    const wsUrl = SERVER_URL.replace('http', 'ws');
    const ws = new WebSocket(`${wsUrl}/ws/download/${jobId}`);
    
    ws.onmessage = async (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === 'progress') {
        setProgress({ percent: msg.percent || 0, status: 'Téléchargement sur le serveur...', speed: msg.speed });
      } else if (msg.type === 'status') {
        setProgress({ percent: progress?.percent || 0, status: msg.message });
      } else if (msg.type === 'completed') {
        ws.close();
        setProgress({ percent: 100, status: 'Finalisation et téléchargement...' });
        await downloadToDevice(jobId, ext);
      } else if (msg.type === 'error') {
        ws.close();
        setDownloading(false);
        setErrorMsg(msg.message);
      }
    };
    
    ws.onerror = (e) => {
       setProgress({ percent: 0, status: 'Erreur WebSocket, le serveur met du temps à répondre...' });
    };
  };

  const downloadToDevice = async (jobId: string, ext: string) => {
    try {
      const resultUrl = `${SERVER_URL}/api/files/${jobId}`;
      
      if (Platform.OS === 'web') {
        const link = document.createElement('a');
        link.href = resultUrl;
        link.download = `mediaflow_${Date.now()}.${ext}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setDownloading(false);
        return;
      }

      const fileUri = FileSystem.documentDirectory + `mediaflow_${Date.now()}.${ext}`; 
      
      const downloadRes = await FileSystem.downloadAsync(resultUrl, fileUri);
      
      if (downloadRes.status === 200) {
        setDownloading(false);
        if (await Sharing.isAvailableAsync()) {
           await Sharing.shareAsync(downloadRes.uri, {
              dialogTitle: 'Enregistrer dans vos fichiers / Photos',
              UTI: ext === 'mp3' ? 'public.audio' : 'public.movie'
           });
        }
      } else {
         setDownloading(false);
         setErrorMsg('Échec du transfert vers l\'iPhone');
      }
      
    } catch(e: any) {
       setDownloading(false);
       setErrorMsg(e.message);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>MediaFlow</Text>
        <Text style={styles.subtitle}>Serveur Cloud Indépendant</Text>
      </View>
      
      <TextInput
         style={styles.input}
         placeholder="Collez l'URL YouTube / Insta ici..."
         placeholderTextColor="#999"
         autoCapitalize="none"
         autoCorrect={false}
         value={url}
         onChangeText={setUrl}
      />
      
      <View style={styles.buttonRow}>
         <TouchableOpacity style={[styles.button, {flex: 1, marginRight: 10}]} onPress={() => analyzeUrl()} disabled={loading || downloading}>
            <Text style={styles.buttonText}>{loading ? loadingText : 'Analyser'}</Text>
         </TouchableOpacity>

         <TouchableOpacity style={[styles.buttonPaste, {flex: 1}]} onPress={pasteAndAnalyze} disabled={loading || downloading}>
            <Text style={styles.buttonPasteText}>Coller & Lancer</Text>
         </TouchableOpacity>
      </View>

      {/* Cookie management button */}
      <TouchableOpacity 
        style={[styles.cookieButton, hasCookies && styles.cookieButtonActive]} 
        onPress={() => setShowCookieModal(true)}
      >
        <Text style={styles.cookieButtonText}>
          ⚙️ Cookies YouTube {hasCookies ? '✅' : '(non configurés)'}
        </Text>
      </TouchableOpacity>

      {errorMsg ? (
        <View style={styles.errorBox}>
           <Text style={styles.errorText}>{errorMsg}</Text>
           {(errorMsg.includes('cookie') || errorMsg.includes('Cookie') || errorMsg.includes('bot')) && (
             <TouchableOpacity style={styles.cookieFixButton} onPress={() => setShowCookieModal(true)}>
               <Text style={styles.cookieFixButtonText}>Configurer les cookies →</Text>
             </TouchableOpacity>
           )}
        </View>
      ) : null}

      {downloading && progress && (
        <View style={styles.progressContainer}>
           <Text style={styles.progressText}>{progress.status}</Text>
           <View style={styles.progressBarBg}>
              <View style={[styles.progressBarFill, { width: `${Math.min(100, progress.percent)}%` }]} />
           </View>
        </View>
      )}

      {mediaData && !downloading && (
        <ScrollView style={styles.resultsContainer} showsVerticalScrollIndicator={false}>
           <Text style={styles.resTitle}>{mediaData.media.title}</Text>
           <Text style={styles.resSub}>{mediaData.media.duration_str} - {mediaData.media.platform}</Text>
           
           <Text style={styles.sectionTitle}>Formats Vidéo</Text>
           {mediaData.video_formats.slice(0, 6).map((fmt: any) => (
             <TouchableOpacity key={fmt.format_id} style={styles.formatBtn} onPress={() => startDownload(fmt, false)}>
               <Text style={styles.formatText}>{fmt.label}</Text>
             </TouchableOpacity>
           ))}

           <Text style={styles.sectionTitle}>Formats Audio</Text>
           {mediaData.audio_formats.slice(0, 4).map((fmt: any) => (
             <TouchableOpacity key={fmt.format_id} style={styles.formatBtnAudio} onPress={() => startDownload(fmt, true)}>
               <Text style={styles.formatText}>{fmt.label}</Text>
             </TouchableOpacity>
           ))}
           <View style={{height: 100}} />
        </ScrollView>
      )}

      {/* Cookie Modal */}
      <Modal
        visible={showCookieModal}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setShowCookieModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>🍪 Cookies YouTube</Text>
            <Text style={styles.modalDesc}>
              YouTube bloque les serveurs cloud. Pour débloquer, exportez vos cookies YouTube depuis votre navigateur et collez-les ici.
            </Text>
            
            <Text style={styles.modalSteps}>
              1. Installez l'extension "Get cookies.txt LOCALLY", que vous pouvez télécharger <Text style={{color: '#007AFF', textDecorationLine: 'underline'}} onPress={() => Linking.openURL('https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc')}>ici</Text> dans Chrome/Edge{'\n'}
              2. Allez sur youtube.com (connecté à votre compte){'\n'}
              3. Cliquez sur l'extension → Exporter{'\n'}
              4. Copiez tout le contenu et collez-le ci-dessous
            </Text>

            <TextInput
              style={styles.cookieInput}
              placeholder="Collez le contenu de cookies.txt ici..."
              placeholderTextColor="#666"
              multiline
              numberOfLines={6}
              value={cookieText}
              onChangeText={setCookieText}
            />

            <View style={styles.modalButtons}>
              <TouchableOpacity 
                style={[styles.modalBtn, styles.modalBtnPrimary]} 
                onPress={uploadCookies}
                disabled={cookieLoading}
              >
                <Text style={styles.modalBtnText}>
                  {cookieLoading ? 'Envoi...' : 'Enregistrer'}
                </Text>
              </TouchableOpacity>

              {hasCookies && (
                <TouchableOpacity 
                  style={[styles.modalBtn, styles.modalBtnDanger]} 
                  onPress={deleteCookies}
                >
                  <Text style={styles.modalBtnText}>Supprimer</Text>
                </TouchableOpacity>
              )}

              <TouchableOpacity 
                style={[styles.modalBtn, styles.modalBtnCancel]} 
                onPress={() => setShowCookieModal(false)}
              >
                <Text style={styles.modalBtnTextCancel}>Fermer</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
    padding: 20,
    paddingTop: Platform.OS === 'ios' ? 60 : 40,
  },
  header: {
    marginBottom: 20,
    alignItems: 'center',
  },
  title: {
    color: '#fff',
    fontSize: 28,
    fontWeight: '900',
  },
  subtitle: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: '600',
  },
  input: {
    backgroundColor: '#1e1e1e',
    color: '#fff',
    padding: 15,
    borderRadius: 12,
    fontSize: 16,
    marginBottom: 15,
    borderWidth: 1,
    borderColor: '#333',
  },
  buttonRow: {
    flexDirection: 'row',
    marginBottom: 5,
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#007AFF',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 5,
  },
  buttonPaste: {
    backgroundColor: '#ff9500',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#ff9500',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 5,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  buttonPasteText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  cookieButton: {
    marginTop: 10,
    padding: 10,
    borderRadius: 8,
    backgroundColor: '#1e1e1e',
    borderWidth: 1,
    borderColor: '#333',
    alignItems: 'center',
  },
  cookieButtonActive: {
    borderColor: '#34c759',
    backgroundColor: 'rgba(52, 199, 89, 0.1)',
  },
  cookieButtonText: {
    color: '#aaa',
    fontSize: 13,
  },
  cookieFixButton: {
    marginTop: 10,
    padding: 10,
    backgroundColor: '#007AFF',
    borderRadius: 8,
    alignItems: 'center',
  },
  cookieFixButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  resultsContainer: {
    marginTop: 25,
  },
  errorBox: {
    marginTop: 15,
    backgroundColor: 'rgba(255, 0, 0, 0.1)',
    padding: 15,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'red',
  },
  errorText: {
    color: '#ff4d4d',
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  resTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  resSub: {
    color: '#aaa',
    marginBottom: 20,
    fontSize: 14,
  },
  sectionTitle: {
    color: '#ddd',
    fontSize: 14,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginTop: 10,
    marginBottom: 10,
  },
  formatBtn: {
    backgroundColor: '#2a2a2a',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#333',
  },
  formatBtnAudio: {
    backgroundColor: '#1a2530',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#2c3e50',
  },
  formatText: {
    color: '#fff',
    fontSize: 15,
  },
  progressContainer: {
    marginTop: 30,
    padding: 20,
    backgroundColor: '#1e1e1e',
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#333',
  },
  progressText: {
    color: '#fff',
    fontSize: 15,
    marginBottom: 15,
    textAlign: 'center',
  },
  progressBarBg: {
    width: '100%',
    height: 8,
    backgroundColor: '#333',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#007AFF',
    borderRadius: 4,
  },
  // Cookie Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.85)',
    justifyContent: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#1e1e1e',
    borderRadius: 16,
    padding: 24,
    borderWidth: 1,
    borderColor: '#333',
  },
  modalTitle: {
    color: '#fff',
    fontSize: 22,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
  },
  modalDesc: {
    color: '#ccc',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 15,
    lineHeight: 20,
  },
  modalSteps: {
    color: '#aaa',
    fontSize: 13,
    marginBottom: 15,
    lineHeight: 20,
    backgroundColor: '#161616',
    padding: 12,
    borderRadius: 8,
  },
  cookieInput: {
    backgroundColor: '#0d0d0d',
    color: '#fff',
    padding: 12,
    borderRadius: 8,
    fontSize: 12,
    minHeight: 120,
    borderWidth: 1,
    borderColor: '#333',
    textAlignVertical: 'top',
    fontFamily: Platform.OS === 'web' ? 'monospace' : undefined,
    marginBottom: 15,
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 10,
  },
  modalBtn: {
    flex: 1,
    padding: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  modalBtnPrimary: {
    backgroundColor: '#34c759',
  },
  modalBtnDanger: {
    backgroundColor: '#ff3b30',
  },
  modalBtnCancel: {
    backgroundColor: '#333',
  },
  modalBtnText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 15,
  },
  modalBtnTextCancel: {
    color: '#aaa',
    fontWeight: 'bold',
    fontSize: 15,
  },
});
