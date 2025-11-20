import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import Icon from '@/components/ui/icon';
import { useToast } from '@/hooks/use-toast';

const AUTH_URL = 'https://functions.poehali.dev/b0b7286b-dd21-40f9-aa8b-708e1c01bd9f';
const CONTACTS_URL = 'https://functions.poehali.dev/0de765d4-97ed-477f-9bd6-252ef21cd7c3';

type User = {
  id: number;
  email: string;
  name: string;
  avatar_url: string | null;
};

type Contact = {
  id: number;
  email: string;
  name: string;
  avatar_url: string | null;
  added_at?: string;
};

type ContactRequest = {
  request_id: number;
  user_id: number;
  email: string;
  name: string;
  avatar_url: string | null;
  created_at: string;
};

const Index = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'contacts' | 'requests' | 'search' | 'profile'>('contacts');
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [requests, setRequests] = useState<ContactRequest[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<User[]>([]);
  
  const { toast } = useToast();

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const action = authMode === 'login' ? 'login' : 'register';
      const body = authMode === 'login' 
        ? { action, email, password }
        : { action, email, password, name };
      
      const response = await fetch(AUTH_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setUser(data.user);
        setToken(data.token);
        setIsLoggedIn(true);
        toast({ title: authMode === 'login' ? 'Вы вошли в систему' : 'Регистрация успешна' });
        loadContacts(data.token);
      } else {
        toast({ title: 'Ошибка', description: data.error, variant: 'destructive' });
      }
    } catch (error) {
      toast({ title: 'Ошибка', description: 'Не удалось выполнить запрос', variant: 'destructive' });
    }
  };

  const loadContacts = async (userToken: string) => {
    try {
      const response = await fetch(`${CONTACTS_URL}?action=list`, {
        headers: { 'X-User-Token': userToken },
      });
      const data = await response.json();
      setContacts(data.contacts || []);
    } catch (error) {
      console.error('Error loading contacts:', error);
    }
  };

  const loadRequests = async () => {
    try {
      const response = await fetch(`${CONTACTS_URL}?action=requests`, {
        headers: { 'X-User-Token': token },
      });
      const data = await response.json();
      setRequests(data.requests || []);
    } catch (error) {
      console.error('Error loading requests:', error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    try {
      const response = await fetch(CONTACTS_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Token': token,
        },
        body: JSON.stringify({ action: 'search', query: searchQuery }),
      });
      
      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (error) {
      toast({ title: 'Ошибка поиска', variant: 'destructive' });
    }
  };

  const sendContactRequest = async (contactEmail: string) => {
    try {
      const response = await fetch(CONTACTS_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Token': token,
        },
        body: JSON.stringify({ action: 'send_request', contact_email: contactEmail }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        toast({ title: 'Заявка отправлена' });
        setSearchResults([]);
        setSearchQuery('');
      } else {
        toast({ title: 'Ошибка', description: data.error, variant: 'destructive' });
      }
    } catch (error) {
      toast({ title: 'Ошибка', variant: 'destructive' });
    }
  };

  const handleRequest = async (requestId: number, action: 'accept' | 'reject') => {
    try {
      const response = await fetch(CONTACTS_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Token': token,
        },
        body: JSON.stringify({ action: 'handle_request', request_id: requestId, action }),
      });
      
      if (response.ok) {
        toast({ title: action === 'accept' ? 'Заявка принята' : 'Заявка отклонена' });
        loadRequests();
        if (action === 'accept') loadContacts(token);
      }
    } catch (error) {
      toast({ title: 'Ошибка', variant: 'destructive' });
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUser(null);
    setToken('');
    setContacts([]);
    setRequests([]);
    setEmail('');
    setPassword('');
    setName('');
  };

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center p-4">
        <Card className="w-full max-w-md p-8 shadow-sm border border-gray-100">
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-light text-gray-900 mb-2">Скам 2.0</h1>
            <p className="text-sm text-gray-500">Управляйте вашими связями</p>
          </div>

          <div className="flex gap-2 mb-6">
            <Button
              variant={authMode === 'login' ? 'default' : 'ghost'}
              onClick={() => setAuthMode('login')}
              className="flex-1"
            >
              Вход
            </Button>
            <Button
              variant={authMode === 'register' ? 'default' : 'ghost'}
              onClick={() => setAuthMode('register')}
              className="flex-1"
            >
              Регистрация
            </Button>
          </div>

          <form onSubmit={handleAuth} className="space-y-4">
            {authMode === 'register' && (
              <div>
                <Input
                  placeholder="Имя"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="h-12"
                />
              </div>
            )}
            
            <div>
              <Input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="h-12"
              />
            </div>

            <div>
              <Input
                type="password"
                placeholder="Пароль"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="h-12"
              />
            </div>

            <Button type="submit" className="w-full h-12 text-base">
              {authMode === 'login' ? 'Войти' : 'Зарегистрироваться'}
            </Button>
          </form>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-xl font-light text-gray-900">Скам 2.0</h1>
            
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">{user?.name}</span>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <Icon name="LogOut" size={18} />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <nav className="flex gap-2 mb-8 overflow-x-auto">
          <Button
            variant={activeTab === 'contacts' ? 'default' : 'ghost'}
            onClick={() => {
              setActiveTab('contacts');
              loadContacts(token);
            }}
            className="whitespace-nowrap"
          >
            <Icon name="Users" size={18} className="mr-2" />
            Контакты
          </Button>
          
          <Button
            variant={activeTab === 'requests' ? 'default' : 'ghost'}
            onClick={() => {
              setActiveTab('requests');
              loadRequests();
            }}
            className="whitespace-nowrap"
          >
            <Icon name="Inbox" size={18} className="mr-2" />
            Заявки
          </Button>
          
          <Button
            variant={activeTab === 'search' ? 'default' : 'ghost'}
            onClick={() => setActiveTab('search')}
            className="whitespace-nowrap"
          >
            <Icon name="Search" size={18} className="mr-2" />
            Поиск
          </Button>
          
          <Button
            variant={activeTab === 'profile' ? 'default' : 'ghost'}
            onClick={() => setActiveTab('profile')}
            className="whitespace-nowrap"
          >
            <Icon name="User" size={18} className="mr-2" />
            Профиль
          </Button>
        </nav>

        {activeTab === 'contacts' && (
          <div className="space-y-3">
            <h2 className="text-2xl font-light text-gray-900 mb-6">Мои контакты</h2>
            
            {contacts.length === 0 ? (
              <Card className="p-12 text-center border-dashed">
                <Icon name="Users" size={48} className="mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500">У вас пока нет контактов</p>
                <p className="text-sm text-gray-400 mt-2">Найдите людей через поиск</p>
              </Card>
            ) : (
              contacts.map((contact) => (
                <Card key={contact.id} className="p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-4">
                    <Avatar>
                      <AvatarFallback>{contact.name[0]}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{contact.name}</h3>
                      <p className="text-sm text-gray-500">{contact.email}</p>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        )}

        {activeTab === 'requests' && (
          <div className="space-y-3">
            <h2 className="text-2xl font-light text-gray-900 mb-6">Входящие заявки</h2>
            
            {requests.length === 0 ? (
              <Card className="p-12 text-center border-dashed">
                <Icon name="Inbox" size={48} className="mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500">Нет новых заявок</p>
              </Card>
            ) : (
              requests.map((request) => (
                <Card key={request.request_id} className="p-4">
                  <div className="flex items-center gap-4">
                    <Avatar>
                      <AvatarFallback>{request.name[0]}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{request.name}</h3>
                      <p className="text-sm text-gray-500">{request.email}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => handleRequest(request.request_id, 'accept')}
                      >
                        <Icon name="Check" size={16} />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleRequest(request.request_id, 'reject')}
                      >
                        <Icon name="X" size={16} />
                      </Button>
                    </div>
                  </div>
                </Card>
              ))
            )}
          </div>
        )}

        {activeTab === 'search' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-light text-gray-900">Поиск людей</h2>
            
            <div className="flex gap-2">
              <Input
                placeholder="Введите имя или email"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1 h-12"
              />
              <Button onClick={handleSearch} className="h-12 px-6">
                <Icon name="Search" size={18} />
              </Button>
            </div>

            <div className="space-y-3">
              {searchResults.map((result) => (
                <Card key={result.id} className="p-4">
                  <div className="flex items-center gap-4">
                    <Avatar>
                      <AvatarFallback>{result.name[0]}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{result.name}</h3>
                      <p className="text-sm text-gray-500">{result.email}</p>
                    </div>
                    <Button onClick={() => sendContactRequest(result.email)} size="sm">
                      <Icon name="UserPlus" size={16} className="mr-2" />
                      Добавить
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'profile' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-light text-gray-900">Профиль</h2>
            
            <Card className="p-8">
              <div className="flex items-center gap-6 mb-8">
                <Avatar className="w-20 h-20">
                  <AvatarFallback className="text-2xl">{user?.name[0]}</AvatarFallback>
                </Avatar>
                <div>
                  <h3 className="text-xl font-medium text-gray-900">{user?.name}</h3>
                  <p className="text-gray-500">{user?.email}</p>
                </div>
              </div>

              <div className="space-y-4 border-t pt-6">
                <div>
                  <label className="text-sm text-gray-500">Всего контактов</label>
                  <p className="text-2xl font-light text-gray-900">{contacts.length}</p>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default Index;