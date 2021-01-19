# 1、简介
这是 Android 进阶笔记第三篇，greenDAO 的源码分析，greenDAO 是一个开源的 ORM（对象关系映射），简单来讲通过对象和数据库之间映射的元数据，完成关系型数据的操作技术，如果你有后台开发经验，一定不会陌生。下面我们来看一看 greenDAO 的入门使用。
# 2、入门
## 2.1 配置 greenDAO 插件和库
```java
//项目下 build.gradle
 dependencies {
        ......
        classpath 'org.greenrobot:greendao-gradle-plugin:3.2.2' 
    }

// app下 build.gradle
apply plugin: 'org.greenrobot.greendao'

dependencies {
    ...
     implementation 'org.greenrobot:greendao:3.2.2'
}
```
## 2.2 创建一个实体类
```java
@Entity(nameInDb = "tb_student")
public class StudentEntity {
    @Id(autoincrement = true)
    private Long id;
    private String name;
    private int age;
}    
```
## 2.3 Make Project
用小锤子锤一下，新建的实体类，就会变了，并且会生成 **DaoMaster**、**DaoSession**、**StudentEntityDao**。
```java
@Entity(nameInDb = "tb_student")
public class StudentEntity {
    @Id(autoincrement = true)
    private Long id;
    private String name;
    private int age;
    @Generated(hash = 1440864641)
    public StudentEntity(Long id, String name, int age) {
        this.id = id;
        this.name = name;
        this.age = age;
    }
    @Generated(hash = 634333355)
    public StudentEntity() {
    }
    public Long getId() {
        return this.id;
    }
    public void setId(Long id) {
        this.id = id;
    }
    public String getName() {
        return this.name;
    }
    public void setName(String name) {
        this.name = name;
    }
    public int getAge() {
        return this.age;
    }
    public void setAge(int age) {
        this.age = age;
    }
}
```
| 类名       | 作用                                                         |
| ---------- | ------------------------------------------------------------ |
| DaoMaster  | 负责整个库运行，内部静态类 DatabaseOpenHelper 继承 SQLiteOpenHelper并重写 |
| DaoSession | 操作DAO具体对象，例如 DAO 对象注册                           |
| XXXDao     | 生成DAO对象，用于数据库操作                                  |
## 2.4 初始化 greenDAO
```java
//一般在 Application 中
private void initDB(){
   DaoMaster.DevOpenHelper helper = new  DaoMaster.DevOpenHelper(this, "test.db");
   SQLiteDatabase db = helper.getWritableDatabase();
   DaoMaster daoMaster = new DaoMaster(db);
   daoSession = daoMaster.newSession();
}
```
## 2.5 使用
```java
StudentEntityDao studentEntityDao = App.getIntance().getDaosession().getStudentEntityDao();
 //增
studentEntityDao.insert(studentEntity);
 //删
studentEntityDao.delete(studentEntity);
 //改
studentEntityDao.update(studentEntity);
 //查
List<StudentEntity> studentEntityList = studentEntityDao.loadAll();
```
# 3、源码分析
## 3.1 创建DaoMaster内部类DevOpenHelper对象
从上面代码看出，要使用 greenDAO，先要获取 DaoMaster.DevOpenHelper，我们看看里面发生了什么。
```java
// new 一个  DaoMaster.DevOpenHelper 对象
DaoMaster.DevOpenHelper helper = new  DaoMaster.DevOpenHelper(this, "test.db");

public static class DevOpenHelper extends OpenHelper {
        public DevOpenHelper(Context context, String name) {
            super(context, name);
        }

        public DevOpenHelper(Context context, String name, CursorFactory factory) {
            super(context, name, factory);
        }

        @Override
        public void onUpgrade(Database db, int oldVersion, int newVersion) {
            Log.i("greenDAO", "Upgrading schema from version " + oldVersion + " to " + newVersion + " by dropping all tables");
            dropAllTables(db, true);
            onCreate(db);
        }
}

public static abstract class OpenHelper extends DatabaseOpenHelper {
       public OpenHelper(Context context, String name) {
           super(context, name, SCHEMA_VERSION);
       }

       public OpenHelper(Context context, String name, CursorFactory factory) {
           super(context, name, factory, SCHEMA_VERSION);
       }

       @Override
       public void onCreate(Database db) {
           Log.i("greenDAO", "Creating tables for schema version " + SCHEMA_VERSION);
           createAllTables(db, false);
       }
}

public abstract class DatabaseOpenHelper extends SQLiteOpenHelper {
   ......
}
```
从上面代码我们可以登出结论 DevOpenHelper 间接继承了 SQLiteOpenHelper，众所周知，SQLiteOpenHelper是SQLiteDatabse的一个帮助类，用来管理数据的创建和版本更新。接下来我们重点看 DevOpenHelper 这个类里面干了什么。
```java
/**
*实现了SQLiteOpenHelper的一个帮助类
*/
public abstract class DatabaseOpenHelper extends SQLiteOpenHelper {
    ......
    
    //获取数据库
    public Database getWritableDb() {
        return wrap(getWritableDatabase());
    }

    //1.标准型的数据库：StandardDatabase
    protected Database wrap(SQLiteDatabase sqLiteDatabase) {
        return new StandardDatabase(sqLiteDatabase);
    }
    //2.加密型的数据库：EncryptedDatabase
    public Database getEncryptedWritableDb(String password) {
        EncryptedHelper encryptedHelper = checkEncryptedHelper();
        return encryptedHelper.wrap(encryptedHelper.getWritableDatabase(password));
    }
    ......
    
    private class EncryptedHelper extends net.sqlcipher.database.SQLiteOpenHelper {
        public EncryptedHelper(Context context, String name, int version, boolean loadLibs) {
            super(context, name, null, version);
            if (loadLibs) {
                net.sqlcipher.database.SQLiteDatabase.loadLibs(context);
            }
        }

        @Override
        public void onCreate(net.sqlcipher.database.SQLiteDatabase db) {
            DatabaseOpenHelper.this.onCreate(wrap(db));
        }

        @Override
        public void onUpgrade(net.sqlcipher.database.SQLiteDatabase db, int oldVersion, int newVersion) {
            DatabaseOpenHelper.this.onUpgrade(wrap(db), oldVersion, newVersion);
        }

        @Override
        public void onOpen(net.sqlcipher.database.SQLiteDatabase db) {
            DatabaseOpenHelper.this.onOpen(wrap(db));
        }

        protected Database wrap(net.sqlcipher.database.SQLiteDatabase sqLiteDatabase) {
            return new EncryptedDatabase(sqLiteDatabase);
        }

    }
}

```
从上面代码可以看出，DatabaseOpenHelper 本质上就是实现了SQLiteOpenHelper的一个帮助类，内部能创建两种数据库：
 -  标准型数据库 StandardDatabase
 -  加密型数据库 EncryptedDatabase

```java
//1.标准型数据库 StandardDatabase
public class StandardDatabase implements Database {

    // 这里的SQLiteDatabase是android.database.sqlite.SQLiteDatabase包下的
    private final SQLiteDatabase delegate;

    public StandardDatabase(SQLiteDatabase delegate) {
        this.delegate = delegate;
    }
    ......
}

//2.加密型数据库 EncryptedDatabase
public class EncryptedDatabaseStatement implements DatabaseStatement     {

    // 这里的SQLiteStatement是net.sqlcipher.database.SQLiteStatement包下的
    private final SQLiteStatement delegate;

    public EncryptedDatabaseStatement(SQLiteStatement delegate) {
        this.delegate = delegate;
    }
    ......
}
```
如果您的项目需要使用加密数据库可以使用，helper.getEncryptedWritableDb() 获取加密数据库。加密型数据库 EncryptedDatabase 和 标准型数据库 StandardDatabase 内部都采用代理模式，来创建具体实现。
## 3.2 创建DaoMaster对象
紧接着第二步，创建DaoMaster对象。
```java
SQLiteDatabase db = helper.getWritableDatabase();
DaoMaster daoMaster = new DaoMaster(db)

//DaoMaster.java
public class DaoMaster extends AbstractDaoMaster {
//需要传入 SQLiteDatabase 
   public DaoMaster(SQLiteDatabase db) {
       this(new StandardDatabase(db));
   }

   public DaoMaster(Database db) {
       super(db, SCHEMA_VERSION);
       //注册 DAO 类
       registerDaoClass(StudentEntityDao.class);
    }
}

//AbstractDaoMaster.java
public abstract class AbstractDaoMaster {
    protected final Database db;
    protected final int schemaVersion;
    protected final Map<Class<? extends AbstractDao<?, ?>>, DaoConfig> daoConfigMap;
    public AbstractDaoMaster(Database db, int schemaVersion) {
        this.db = db;
        this.schemaVersion = schemaVersion;
        this.daoConfigMap = new HashMap();
    }
}

protected void registerDaoClass(Class<? extends AbstractDao<?, ?>> daoClass) {
    //DaoConfig 通过反射 得到 DAO 类的属性
    DaoConfig daoConfig = new DaoConfig(this.db, daoClass);
    //保存到集合中
    this.daoConfigMap.put(daoClass, daoConfig);
}

```


## 3.3 创建DaoSession对象

接下来创建 DaoSession
```java
daoSession = daoMaster.newSession();
//DaoMaster#newSession
public DaoSession newSession() {
       //通过daoConfigMap和其他信息生成DaoSession对象
      return new DaoSession(db, IdentityScopeType.Session, daoConfigMap);
}

//DaoSession.java
public class DaoSession extends AbstractDaoSession {
    private final DaoConfig studentEntityDaoConfig;
    private final StudentEntityDao studentEntityDao;
    public DaoSession(Database db, IdentityScopeType type, Map<Class<? extends AbstractDao<?, ?>>, DaoConfig>
            daoConfigMap) {
        //1.调用父类    
        super(db);
        //2.通过daoConfigMap集合得到对应的DaoConfig对象, 然后clone
        studentEntityDaoConfig = daoConfigMap.get(StudentEntityDao.class).clone();
        //3.根据IdentityScopeType的类型初始化创建一个相应的IdentityScope
        //3.1 主键是数字类型 使用 IdentityScopeLong缓存实体数据
        //3.2 不是数字类型 使用IdentityScopeLong缓存实体数据
        studentEntityDaoConfig.initIdentityScope(type);
        //4.得到 studentEntityDao 对象
        studentEntityDao = new StudentEntityDao(studentEntityDaoConfig, this);
        //5.将对象和 DAO 关联起来
        registerDao(StudentEntity.class, studentEntityDao);
    }
    public void clear() {
        studentEntityDaoConfig.clearIdentityScope();
    }
    public StudentEntityDao getStudentEntityDao() {
        return studentEntityDao;
    }
}
//AbstractDaoSession.java
public class AbstractDaoSession {
    ......
    public AbstractDaoSession(Database db) {
        this.db = db;
        //创建一个实体与DAO对象的映射集合
        this.entityToDao = new HashMap<Class<?>, AbstractDao<?, ?>>();
    }
protected <T> void registerDao(Class<T> entityClass, AbstractDao<T, ?> dao) {
        entityToDao.put(entityClass, dao);
    }
```
## 3.4 insert 源码分析
接下来，看看 insert 源码分析
```java
//通过 Daosession 获取 DAO 对象
StudentEntityDao studentEntityDao = App.getIntance().getDaosession().getStudentEntityDao();
studentEntityDao.insert(studentEntity);
```
我们来看看生成的 DAO 是什么样子，如果你有后台开发经验，你会发现简直在某些方面和后台数据库操作神似。
```java
public class StudentEntityDao extends AbstractDao<StudentEntity, Long> {
   ......
}

//所有通用操作的基类
public abstract class AbstractDao<T, K> {
     //插入操作
     public long insert(T entity) {
        //实体、具体数据库操作
        return executeInsert(entity, statements.getInsertStatement(), true);
    }
   
//TableStatements.java 作用：具体数据库操作，向数据库发送要执行的SQL语句
public class TableStatements {
    public DatabaseStatement getInsertStatement() {
        if (insertStatement == null) {
            String sql = SqlUtils.createSqlInsert("INSERT INTO ", tablename, allColumns);
            DatabaseStatement newInsertStatement = db.compileStatement(sql);
            synchronized (this) {
                if (insertStatement == null) {
                    insertStatement = newInsertStatement;
                }
            }
            if (insertStatement != newInsertStatement) {
                newInsertStatement.close();
            }
        }
        return insertStatement;
    }
}

//executeInsert 执行
 private long executeInsert(T entity, DatabaseStatement stmt, boolean setKeyAndAttach) {
        long rowId;
        //当前数据库是否被当前线程锁定
        if (db.isDbLockedByCurrentThread()) {
           //是，直接插入，获取生成的主键
            rowId = insertInsideTx(entity, stmt);
        } else {
            //否，开启事务
            db.beginTransaction();
            try {
               //插入数据
                rowId = insertInsideTx(entity, stmt);
                db.setTransactionSuccessful();
            } finally {
                db.endTransaction();
            }
        }
        //如果设置了主键，更新主键的值，将缓存到identityScope中
        if (setKeyAndAttach) {
            updateKeyAfterInsertAndAttach(entity, rowId, true);
        }
        return rowId;
    }
}

//insertInsideTx 插入数据
private long insertInsideTx(T entity, DatabaseStatement stmt) {
    //加锁，保证数据数据一致性
    synchronized (stmt) {
        //如果是标准数据库 
        if (isStandardSQLite) {
            //获取stmt的原始语句
            SQLiteStatement rawStmt = (SQLiteStatement) stmt.getRawStatement();
            //进行实体字段属性的绑定
            bindValues(rawStmt, entity);
            //插入操作
            return rawStmt.executeInsert();
        } else {
            bindValues(stmt, entity);
            return stmt.executeInsert();
        }
    }
}

//StudentEntityDao#bindValue
//对实体类所有字段使用对应数据库语句进行绑定操作
@Override
protected final void bindValues(DatabaseStatement stmt, StudentEntity entity) {
        stmt.clearBindings();
 
        Long id = entity.getId();
        if (id != null) {
            stmt.bindLong(1, id);
        }
 
        String name = entity.getName();
        if (name != null) {
            stmt.bindString(2, name);
        }
        stmt.bindLong(3, entity.getAge());
    }
```
## 3.5 select 源码分析
其他几个数据库操作流程都差不多，这里就不细写，我们来看看查询的操作，
```java
 //查询
List<StudentEntity> studentEntityList = studentEntityDao.loadAll(studentEntity);
```
会调用 loadAll，我们看看 loadAll 里面干了什么
```java
public List<T> loadAll() {
      Cursor cursor = db.rawQuery(statements.getSelectAll(), null);
      return loadAllAndCloseCursor(cursor);
}
//最后走到 AbstractDao类的loadAllFromCursor方法
 protected List<T> loadAllFromCursor(Cursor cursor) {
        int count = cursor.getCount();
        if (count == 0) {
            return new ArrayList<T>();
        }
        List<T> list = new ArrayList<T>(count);
        CursorWindow window = null;
        boolean useFastCursor = false;
        //如果是跨进程游标
        if (cursor instanceof CrossProcessCursor) {
            window = ((CrossProcessCursor) cursor).getWindow();
            if (window != null) { // E.g. Robolectric has no Window at this point
                if (window.getNumRows() == count) {
                     //加快版游标
                    cursor = new FastCursor(window);
                    useFastCursor = true;
                } else {
                    DaoLog.d("Window vs. result size: " + window.getNumRows() + "/" + count);
                }
            }
        }
        //游标移动
        if (cursor.moveToFirst()) {
            if (identityScope != null) {
                identityScope.lock();
                identityScope.reserveRoom(count);
            }

            try {
                if (!useFastCursor && window != null && identityScope != null) {
                    loadAllUnlockOnWindowBounds(cursor, window, list);
                } else {
                    do {
                        //加载数据
                        list.add(loadCurrent(cursor, 0, false));
                    } while (cursor.moveToNext());
                }
            } finally {
                if (identityScope != null) {
                    identityScope.unlock();
                }
            }
        }
        return list;
    }
/*
*实体数据缓存
*如果有缓存数据，先从缓存数据中取
*/
 final protected T loadCurrent(Cursor cursor, int offset, boolean lock) {
        if (identityScopeLong != null) {
            if (offset != 0) {
                // Occurs with deep loads (left outer joins)
                if (cursor.isNull(pkOrdinal + offset)) {
                    return null;
                }
            }

            long key = cursor.getLong(pkOrdinal + offset);
            T entity = lock ? identityScopeLong.get2(key) : identityScopeLong.get2NoLock(key);
            //有缓存，直接返回
            if (entity != null) {
                return entity;
            } else {
               //否者 根据游标，和偏移数 取出 实体数据
                entity = readEntity(cursor, offset);
                attachEntity(entity);
                if (lock) {
                    identityScopeLong.put2(key, entity);
                } else {
                    identityScopeLong.put2NoLock(key, entity);
                }
                return entity;
            }
        } else if (identityScope != null) {
            K key = readKey(cursor, offset);
            if (offset != 0 && key == null) {
                // Occurs with deep loads (left outer joins)
                return null;
            }
            T entity = lock ? identityScope.get(key) : identityScope.getNoLock(key);
            if (entity != null) {
                return entity;
            } else {
                entity = readEntity(cursor, offset);
                attachEntity(key, entity, lock);
                return entity;
            }
        } else {
            // Check offset, assume a value !=0 indicating a potential outer join, so check PK
            if (offset != 0) {
                K key = readKey(cursor, offset);
                if (key == null) {
                    // Occurs with deep loads (left outer joins)
                    return null;
                }
            }
            T entity = readEntity(cursor, offset);
            attachEntity(entity);
            return entity;
        }
    }
```

注意：使用greenDAO查询数据没有拿到最新结果的bug， 如果出现这个bug且需要拿到最新的数据库信息，可以使用DaoSession的clear方法删除缓存。
```java
//DaoSession.java
public void clear() {
      studentEntityDaoConfig.clearIdentityScope();
}

//DaoConfig
public void clearIdentityScope() {
      IdentityScope<?, ?> identityScope = this.identityScope;
      if(identityScope != null) {
           identityScope.clear();
      }
}
```
到这里，greenDAO 具体流程分析差不多。
# 4、参考
[GreenDao源码分析](https://mp.weixin.qq.com/s?__biz=MzIwMTAzMTMxMg==&mid=2649492577&idx=1&sn=b35b0ef0f3769efa8c5d49fc5d60dd80&chksm=8eec879eb99b0e8881dd83cac912192df742ad547ccd274b7fccd2995edd08b095e1fd556cfe&scene=38#wechat_redirect)
[Android主流三方库源码分析（四、深入理解GreenDao源码）](https://jsonchao.github.io/2018/12/22/Android%E4%B8%BB%E6%B5%81%E4%B8%89%E6%96%B9%E5%BA%93%E6%BA%90%E7%A0%81%E5%88%86%E6%9E%90%EF%BC%88%E5%9B%9B%E3%80%81%E6%B7%B1%E5%85%A5%E7%90%86%E8%A7%A3GreenDao%E6%BA%90%E7%A0%81%EF%BC%89/)