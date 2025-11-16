import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Image,
  TouchableOpacity,
  TextInput,
  FlatList,
  Alert,
  ImageBackground,
  ActivityIndicator,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { fonts } from '../theme/typography';
import { deleteScans, fetchRecommendation, listScans } from '../api';
import { useAuth } from '../context/AuthContext';

export default function HistoryScreen({ navigation }) {
  const { token, logout } = useAuth();
  const [history, setHistory] = useState([]);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(new Set());
  const [recommendations, setRecommendations] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) {
      navigation.replace('Login');
    }
  }, [token, navigation]);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const items = await listScans(token);
      const normalized = items.map((item) => {
        const confidence = typeof item.confidence === 'number'
          ? Math.max(0, Math.min(100, Math.round(item.confidence * 1000) / 10))
          : null;
        const createdAt = item.createdAt ? new Date(item.createdAt) : new Date();
        return {
          id: item.id,
          label: item.label ?? 'uncertain',
          confidence,
          timestamp: createdAt,
          notes: item.notes || '',
        };
      });
      setHistory(normalized);

      const uniqueKeys = [...new Set(normalized.map((it) => it.label).filter((label) => label && label !== 'uncertain'))];
      const missingKeys = uniqueKeys.filter((key) => recommendations[key] == null);
      if (missingKeys.length) {
        const entries = await Promise.all(
          missingKeys.map(async (key) => {
            const rec = await fetchRecommendation(key);
            if (rec?.steps?.length) {
              return [key, `${rec.title}\n\u2022 ${rec.steps.join('\n\u2022 ')}`];
            }
            return [key, rec?.title || 'No recommendation available.'];
          }),
        );
        setRecommendations((prev) => ({ ...prev, ...Object.fromEntries(entries) }));
      }
    } catch (err) {
      console.warn('Failed to load scan history', err);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  }, [token, recommendations]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const visibleHistory = useMemo(() => {
    const q = query.trim().toLowerCase();
    return history
      .slice()
      .sort((a, b) => b.timestamp - a.timestamp)
      .filter((item) => {
        if (!q) return true;
        const recText = recommendations[item.label] || '';
        const hay = `${item.label || ''} ${item.notes || ''} ${recText} ${item.timestamp?.toLocaleString?.() || ''}`.toLowerCase();
        return hay.includes(q);
      });
  }, [history, query, recommendations]);

  const toggleSelect = (id) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAllVisible = () => {
    const allSelected = visibleHistory.length > 0 && visibleHistory.every((it) => selected.has(it.id));
    setSelected((prev) => {
      const next = new Set(prev);
      if (allSelected) visibleHistory.forEach((it) => next.delete(it.id));
      else visibleHistory.forEach((it) => next.add(it.id));
      return next;
    });
  };

  const confirmDeleteSelected = () => {
    if (!token) {
      Alert.alert('Login required', 'Please log in to manage your scan history.');
      navigation.replace('Login');
      return;
    }
    const count = selected.size;
    if (count === 0) return;
    Alert.alert('Delete selected', `Delete ${count} selected scan(s)?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          const toDelete = Array.from(selected);
          try {
            await deleteScans(token, toDelete);
            setHistory((prev) => prev.filter((it) => !selected.has(it.id)));
          } catch (err) {
            Alert.alert('Failed to delete', err?.message || 'Please try again.');
          }
          setSelected(new Set());
        },
      },
    ]);
  };

  const confirmDeleteAll = () => {
    if (!token) {
      Alert.alert('Login required', 'Please log in to manage your scan history.');
      navigation.replace('Login');
      return;
    }
    if (history.length === 0) return;
    Alert.alert('Delete all', 'This will permanently delete all scans.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete All',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteScans(token, history.map((it) => it.id));
            setHistory([]);
            setSelected(new Set());
          } catch (err) {
            Alert.alert('Failed to delete', err?.message || 'Please try again.');
          }
        },
      },
    ]);
  };

  return (
    <ImageBackground source={require('../../assets/bg.png')} resizeMode="cover" style={styles.container}>
      <View style={styles.header}>
        <Image source={require('../../assets/logo.png')} style={styles.headerLogo} />
        <View style={styles.navRow}>
          <TouchableOpacity onPress={() => { logout(); navigation.replace('Login'); }}>
            <Text style={styles.navLink}>Log Out</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => navigation.navigate('Scan')}><Text style={styles.navLink}>Scan</Text></TouchableOpacity>
          <Text style={[styles.navLink, styles.navActive]}>History</Text>
        </View>
      </View>

      <View style={styles.toolbar}>
        <Text style={styles.title}>Scan History</Text>
        <View style={styles.controls}>
          <TextInput
            placeholder="Search history..."
            value={query}
            onChangeText={setQuery}
            style={styles.search}
          />
          <TouchableOpacity onPress={toggleSelectAllVisible}><Text style={styles.action}>Select all</Text></TouchableOpacity>
          <TouchableOpacity disabled={selected.size === 0} onPress={confirmDeleteSelected}>
            <Text style={[styles.action, selected.size === 0 && styles.disabled]}>Delete Selected</Text>
          </TouchableOpacity>
          <TouchableOpacity disabled={history.length === 0} onPress={confirmDeleteAll}>
            <Text style={[styles.action, history.length === 0 && styles.disabled]}>Delete All</Text>
          </TouchableOpacity>
        </View>
      </View>

      {history.length === 0 ? (
        loading ? (
          <ActivityIndicator style={{ marginTop: 32 }} />
        ) : (
          <Text style={styles.noHistory}>No history records found.</Text>
        )
      ) : (
        <FlatList
          contentContainerStyle={styles.list}
          data={visibleHistory}
          keyExtractor={(item) => String(item.id)}
          renderItem={({ item }) => (
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <TouchableOpacity onPress={() => toggleSelect(item.id)}>
                  <Text style={styles.checkbox}>{selected.has(item.id) ? '☑' : '☐'}</Text>
                </TouchableOpacity>
              </View>
              <View style={styles.cardBody}>
                <Text style={styles.cardTitle}>{item.label}</Text>
                <Text>
                  <Text style={styles.bold}>Confidence:</Text>{' '}
                  {typeof item.confidence === 'number' ? `${item.confidence.toFixed(1)}%` : 'N/A'}
                </Text>
                {!!item.notes && (
                  <Text>
                    <Text style={styles.bold}>Notes:</Text> {item.notes}
                  </Text>
                )}
                <Text style={styles.bold}>Recommendation:</Text>
                <Text>{recommendations[item.label] || 'No recommendation available.'}</Text>
                <Text>
                  <Text style={styles.bold}>Date:</Text> {item.timestamp?.toLocaleString?.() || ''}
                </Text>
              </View>
            </View>
          )}
        />
      )}
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: { paddingTop: 54, paddingHorizontal: 16, paddingBottom: 12, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#e5e7eb' },
  headerLogo: { width: 70, height: 70, marginBottom: 8 },
  navRow: { flexDirection: 'row', justifyContent: 'flex-end', gap: 16 },
  navLink: { marginLeft: 16, color: '#dbcacaff' },
  navActive: { color: '#ffffffff', fontFamily: fonts.bold },
  toolbar: { paddingHorizontal: 16, paddingVertical: 16, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#ffffffff' },
  title: { fontSize: 30, fontFamily: fonts.bold, marginBottom: 20, color: '#fff', textAlign: 'center' },
  controls: { flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap' },
  search: { flexGrow: 1, minWidth: 160, borderWidth: 1, borderColor: '#ffffffff', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 8, marginRight: 8 },
  action: { marginLeft: 12, color: '#ffffffff', fontFamily: fonts.semi, marginTop: 10 },
  disabled: { color: '#ff1717ff' },
  noHistory: { padding: 24, textAlign: 'center', color: '#e5ecf9ff' },
  list: { padding: 16 },
  card: { borderWidth: 1, borderColor: '#e5e7eb', borderRadius: 12, padding: 12, marginBottom: 12, backgroundColor: '#f9fafb' },
  cardHeader: { flexDirection: 'row', justifyContent: 'flex-end' },
  checkbox: { fontSize: 18 },
  cardBody: { marginTop: 8 },
  cardTitle: { fontSize: 16, fontFamily: fonts.bold, marginBottom: 4 },
  bold: { fontFamily: fonts.bold },
});
