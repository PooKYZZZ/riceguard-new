import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, Image, ImageBackground, Modal, TextInput, KeyboardAvoidingView, Platform, Alert } from 'react-native';
import Button from '../components/Button';
import { fonts } from '../theme/typography';
import { loginUser, registerUser } from '../api';
import { useAuth } from '../context/AuthContext';

export default function LoginScreen({ navigation }) {
  const { token, setAuth } = useAuth();
  const [loginOpen, setLoginOpen] = useState(false);
  const [signupOpen, setSignupOpen] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPass, setSignupPass] = useState('');
  const [signupConfirm, setSignupConfirm] = useState('');
  const [signupError, setSignupError] = useState('');
  const [signupLoading, setSignupLoading] = useState(false);

  useEffect(() => {
    if (token) {
      navigation.replace('Scan');
    }
  }, [token, navigation]);

  const openLogin = () => {
    setLoginError('');
    setLoginOpen(true);
  };
  const closeLogin = () => {
    setLoginOpen(false);
    setUsername('');
    setPassword('');
    setLoginError('');
    setLoginLoading(false);
  };
  const openSignup = () => {
    setSignupError('');
    setSignupOpen(true);
  };
  const closeSignup = () => {
    setSignupOpen(false);
    setSignupEmail('');
    setSignupPass('');
    setSignupConfirm('');
    setSignupError('');
    setSignupLoading(false);
  };

  const submitLogin = async () => {
    const email = username.trim();
    if (!email || !password) {
      setLoginError('Email and password are required.');
      return;
    }
    setLoginError('');
    try {
      setLoginLoading(true);
      const data = await loginUser({ email, password });
      setAuth({ token: data.accessToken, user: data.user, expiresAt: data.expiresAt });
      closeLogin();
      navigation.replace('Scan');
    } catch (err) {
      const message = err?.message || 'Failed to log in. Please try again.';
      setLoginError(message);
      Alert.alert('Login failed', message);
    } finally {
      setLoginLoading(false);
    }
  };

  const submitSignup = async () => {
    setSignupError('');
    const email = signupEmail.trim();
    const emailRegex = /[^\s@]+@[^\s@]+\.[^\s@]+/;
    if (!emailRegex.test(email)) return setSignupError('Please enter a valid email address.');
    if (signupPass.length < 8) return setSignupError('Password must be at least 8 characters long.');
    if (signupPass !== signupConfirm) return setSignupError('Passwords do not match.');
    try {
      setSignupLoading(true);
      const derivedName = email.split('@')[0] || 'RiceGuard User';
      await registerUser({ name: derivedName, email, password: signupPass });
      Alert.alert('Account created', 'You can now log in with your new credentials.');
      closeSignup();
      openLogin();
      setUsername(email);
    } catch (err) {
      setSignupError(err?.message || 'Failed to sign up. Please try again.');
    } finally {
      setSignupLoading(false);
    }
  };

  return (
    <ImageBackground source={require('../../assets/bg.png')} resizeMode="cover" style={styles.container}>
      <Image source={require('../../assets/logo.png')} style={styles.logo} resizeMode="contain" />
      <Text style={styles.tagline}>Your Smart Companion for Healthy Rice Fields</Text>

      <View style={styles.actions}>
        <Button onPress={openLogin} style={styles.greenButton} textStyle={styles.ctaTextLarge}>Log in</Button>
        <Button onPress={openSignup} style={styles.greenButton} textStyle={styles.ctaTextLarge}>Sign Up</Button>
      </View>

      <Modal visible={loginOpen} transparent animationType="fade" onRequestClose={closeLogin}>
        <View style={styles.backdrop}>
          <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.modal}>
            <Image source={require('../../assets/user.png')} style={styles.avatar} />
            <Text style={styles.modalTitle}>Log in</Text>
            <TextInput
              placeholder="Email"
              keyboardType="email-address"
              autoCapitalize="none"
              value={username}
              onChangeText={setUsername}
              style={styles.input}
            />
            <TextInput
              placeholder="Password"
              secureTextEntry
              value={password}
              onChangeText={setPassword}
              style={styles.input}
            />
            {!!loginError && <Text style={styles.errorText}>{loginError}</Text>}
            <View style={styles.modalActions}>
              <Button onPress={closeLogin}style={styles.greenButton2}>Cancel</Button>
              <Button onPress={submitLogin}style={styles.greenButton2} disabled={loginLoading}>
                {loginLoading ? 'Signing in...' : 'Log in'}
              </Button>
            </View>
          </KeyboardAvoidingView>
        </View>
      </Modal>

      <Modal visible={signupOpen} transparent animationType="fade" onRequestClose={closeSignup}>
        <View style={styles.backdrop}>
          <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.modal}>
            <Image source={require('../../assets/user.png')} style={styles.avatar} />
            <Text style={styles.modalTitle}>Sign Up</Text>
            <TextInput
              placeholder="Email"
              keyboardType="email-address"
              autoCapitalize="none"
              value={signupEmail}
              onChangeText={setSignupEmail}
              style={styles.input}
            />
            <TextInput
              placeholder="Password"
              secureTextEntry
              value={signupPass}
              onChangeText={setSignupPass}
              style={styles.input}
            />
            <TextInput
              placeholder="Confirm Password"
              secureTextEntry
              value={signupConfirm}
              onChangeText={setSignupConfirm}
              style={styles.input}
            />
            {!!signupError && <Text style={styles.errorText}>{signupError}</Text>}
            <View style={styles.modalActions}>
              <Button onPress={closeSignup}style={styles.greenButton2}>Cancel</Button>
              <Button onPress={submitSignup}style={styles.greenButton2} disabled={signupLoading}>
                {signupLoading ? 'Creating...' : 'Sign Up'}
              </Button>
            </View>
          </KeyboardAvoidingView>
        </View>
      </Modal>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  logo: { width: 250, height: 250, marginBottom: 16 },
  tagline: { textAlign: 'center', color: '#fff', fontSize: 24, marginBottom: 24 },
  actions: { fontSize:20, flexDirection: 'row', marginTop: 8, color:'#fff' },
  ctaTextLarge: { fontSize: 22 },
  greenButton: { backgroundColor: '#109724ff', borderRadius:100 ,height:65,width:150},
  greenButton2: { backgroundColor: '#109724ff',borderRadius:100},
  backdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', alignItems: 'center', justifyContent: 'center', padding: 16 },
  modal: { width: '100%', maxWidth: 420, backgroundColor: '#fff', borderRadius: 12, padding: 16 },
  avatar: { width: 120, height: 120, alignSelf: 'center', marginBottom: 12 },
  modalTitle: { color: '#01a730ff', fontSize: 30, fontFamily: fonts.bold, textAlign: 'center', marginBottom: 42 },
  input: { borderWidth: 1, borderColor: '#e5e7eb', borderRadius: 8, paddingHorizontal: 12, paddingVertical: 10, marginVertical: 10 },
  modalActions: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: 12 },
  errorText: { color: '#b91c1c', marginTop: 4 },
});
